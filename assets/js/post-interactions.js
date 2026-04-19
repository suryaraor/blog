(function () {
  'use strict';

  var root = document.querySelector('.post-interactions');

  if (!root) {
    return;
  }

  var apiUrl = (root.dataset.apiUrl || '').replace(/\/+$/, '');
  var postId = root.dataset.postId || window.location.pathname;
  var pageUrl = root.dataset.pageUrl || window.location.pathname;
  var postTitle = root.dataset.postTitle || document.title;
  var commentList = root.querySelector('[data-comment-list]');
  var commentCount = root.querySelector('[data-comment-count]');
  var likeCount = root.querySelector('[data-like-count]');
  var likeButton = root.querySelector('[data-like-button]');
  var statusMessage = root.querySelector('[data-status-message]');
  var commentForm = root.querySelector('[data-comment-form]');
  var commentSubmit = root.querySelector('[data-comment-submit]');
  var renderedAtInput = root.querySelector('[data-rendered-at]');
  var visitorIdInput = root.querySelector('[data-visitor-id]');
  var userAgentInput = root.querySelector('[data-user-agent]');
  var loadingClass = 'is-loading';
  var likeStorageKey = 'blog-like:' + postId;
  var visitorStorageKey = 'blog-visitor-id';
  var renderTimestamp = Date.now();
  var minSubmitDelayMs = 4000;
  var loadedState = {
    likes_count: 0,
    liked: false,
    comments: []
  };

  if (!apiUrl) {
    showMessage('Set comments_api_url in _config.yml after deploying the Apps Script web app.', 'error');
    if (likeButton) {
      likeButton.disabled = true;
    }
    return;
  }

  if (renderedAtInput) {
    renderedAtInput.value = String(renderTimestamp);
  }

  if (visitorIdInput) {
    visitorIdInput.value = getOrCreateVisitorId();
  }

  if (userAgentInput) {
    userAgentInput.value = navigator.userAgent || '';
  }

  root.classList.add(loadingClass);
  bindEvents();
  hydrateLikeState();
  loadPostData();

  function bindEvents() {
    if (likeButton) {
      likeButton.addEventListener('click', handleLikeClick);
    }

    if (commentForm) {
      commentForm.addEventListener('submit', handleCommentSubmit);
    }
  }

  function getOrCreateVisitorId() {
    var stored = safeLocalStorageGet(visitorStorageKey);
    if (stored) {
      return stored;
    }

    var generated = generateVisitorId();
    safeLocalStorageSet(visitorStorageKey, generated);
    return generated;
  }

  function generateVisitorId() {
    if (window.crypto && typeof window.crypto.randomUUID === 'function') {
      return window.crypto.randomUUID();
    }

    var random = Math.random().toString(36).slice(2);
    return 'visitor-' + Date.now().toString(36) + '-' + random;
  }

  function safeLocalStorageGet(key) {
    try {
      return window.localStorage.getItem(key);
    } catch (error) {
      return null;
    }
  }

  function safeLocalStorageSet(key, value) {
    try {
      window.localStorage.setItem(key, value);
    } catch (error) {
      return false;
    }

    return true;
  }

  function isLikedLocally() {
    return safeLocalStorageGet(likeStorageKey) === '1';
  }

  function hydrateLikeState() {
    if (!likeButton) {
      return;
    }

    if (isLikedLocally()) {
      likeButton.classList.add('is-liked');
    }
  }

  function setLikeState(liked) {
    if (!likeButton) {
      return;
    }

    likeButton.disabled = liked;
    likeButton.classList.toggle('is-liked', liked);
    likeButton.setAttribute('aria-pressed', liked ? 'true' : 'false');
  }

  function showMessage(message, type) {
    if (!statusMessage) {
      return;
    }

    statusMessage.classList.remove('is-success', 'is-error');
    if (type === 'success') {
      statusMessage.classList.add('is-success');
    } else if (type === 'error') {
      statusMessage.classList.add('is-error');
    }

    statusMessage.textContent = message || '';
  }

  function setLoading(isLoading) {
    root.classList.toggle(loadingClass, Boolean(isLoading));
  }

  function updateCounts(data) {
    if (likeCount && typeof data.likes_count === 'number') {
      likeCount.textContent = String(data.likes_count);
    }

    if (commentCount && Array.isArray(data.comments)) {
      commentCount.textContent = String(data.comments.length);
    } else if (commentCount && typeof data.approved_comments_count === 'number') {
      commentCount.textContent = String(data.approved_comments_count);
    }
  }

  function renderComments(comments) {
    if (!commentList) {
      return;
    }

    commentList.innerHTML = '';

    comments.forEach(function (comment) {
      if (!comment || !comment.comment) {
        return;
      }

      var item = document.createElement('li');
      item.className = 'comment-card';

      var meta = document.createElement('div');
      meta.className = 'comment-card__meta';

      var name = document.createElement('span');
      name.className = 'comment-card__name';
      name.textContent = comment.name || 'Anonymous';
      meta.appendChild(name);

      var created = document.createElement('time');
      created.dateTime = comment.created_at_iso || '';
      created.textContent = formatTimestamp(comment.created_at || comment.created_at_iso);
      meta.appendChild(created);

      if (comment.website) {
        var website = document.createElement('a');
        website.className = 'comment-card__website';
        website.href = comment.website;
        website.rel = 'nofollow noopener noreferrer ugc';
        website.target = '_blank';
        website.textContent = comment.website_label || 'Website';
        meta.appendChild(website);
      }

      var body = document.createElement('p');
      body.className = 'comment-card__body';
      body.textContent = comment.comment;

      item.appendChild(meta);
      item.appendChild(body);
      commentList.appendChild(item);
    });
  }

  function formatTimestamp(value) {
    if (!value) {
      return '';
    }

    var date = new Date(value);
    if (Number.isNaN(date.getTime())) {
      return String(value);
    }

    return new Intl.DateTimeFormat(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    }).format(date);
  }

  function buildUrl(action, params) {
    var url = new URL(apiUrl);
    url.searchParams.set('action', action);
    url.searchParams.set('post_id', postId);
    url.searchParams.set('page_url', pageUrl);
    url.searchParams.set('_', String(Date.now()));

    Object.keys(params || {}).forEach(function (key) {
      if (params[key] !== undefined && params[key] !== null) {
        url.searchParams.set(key, String(params[key]));
      }
    });

    return url.toString();
  }

  async function requestJson(method, action, payload) {
    var options = {
      method: method,
      mode: 'cors',
      credentials: 'omit',
      cache: 'no-store'
    };

    var url = buildUrl(action, payload && method === 'GET' ? payload : {});

    if (method === 'POST') {
      var body = new URLSearchParams();
      body.set('action', action);
      body.set('post_id', postId);
      body.set('page_url', pageUrl);
      body.set('post_title', postTitle);
      body.set('_', String(Date.now()));

      Object.keys(payload || {}).forEach(function (key) {
        if (payload[key] !== undefined && payload[key] !== null) {
          body.set(key, String(payload[key]));
        }
      });

      options.body = body.toString();
      options.headers = {
        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'
      };
    }

    var response = await fetch(url, options);
    var text = await response.text();
    var data;

    try {
      data = JSON.parse(text);
    } catch (error) {
      throw new Error('The comments service returned an invalid response.');
    }

    if (!response.ok || data.ok === false) {
      throw new Error(data.error || 'The comments service request failed.');
    }

    return data;
  }

  async function loadPostData() {
    setLoading(true);
    showMessage('');

    try {
      var data = await requestJson('GET', 'getPostData', {
        visitor_id: getOrCreateVisitorId()
      });

      loadedState = data;
      updateCounts(data);
      setLikeState(Boolean(data.liked || isLikedLocally()));
      renderComments(data.comments || []);
      showMessage('Loaded comments and likes.', 'success');
      return;
    } catch (combinedError) {
      try {
        var commentsData = await requestJson('GET', 'getComments', {});
        var likesData = await requestJson('GET', 'getLikes', {
          visitor_id: getOrCreateVisitorId()
        });

        loadedState = {
          comments: commentsData.comments || [],
          likes_count: likesData.likes_count || 0,
          liked: Boolean(likesData.liked)
        };

        updateCounts(loadedState);
        setLikeState(Boolean(loadedState.liked || isLikedLocally()));
        renderComments(loadedState.comments);
        showMessage('Loaded comments and likes.', 'success');
      } catch (fallbackError) {
        showMessage('Unable to load comments right now. Please refresh later.', 'error');
      }
    } finally {
      setLoading(false);
    }
  }

  async function handleLikeClick() {
    if (!likeButton || likeButton.disabled || isLikedLocally()) {
      return;
    }

    likeButton.disabled = true;
    showMessage('Saving your like...');

    try {
      var data = await requestJson('POST', 'addLike', {
        visitor_id: getOrCreateVisitorId()
      });

      safeLocalStorageSet(likeStorageKey, '1');
      setLikeState(true);
      updateCounts(data);
      showMessage('Thanks for liking this post.', 'success');
    } catch (error) {
      likeButton.disabled = false;
      showMessage(error.message || 'Unable to save your like.', 'error');
    }
  }

  async function handleCommentSubmit(event) {
    event.preventDefault();

    if (!commentForm || !commentSubmit) {
      return;
    }

    var formData = new FormData(commentForm);
    var payload = Object.fromEntries(formData.entries());
    var honeypot = String(payload.company || '').trim();
    var name = String(payload.name || '').trim();
    var comment = String(payload.comment || '').trim();
    var website = String(payload.website || '').trim();
    var renderedAt = Number(payload.rendered_at || 0);
    var delayMs = Date.now() - renderedAt;

    if (honeypot) {
      showMessage('Submission blocked.', 'error');
      return;
    }

    if (delayMs < minSubmitDelayMs) {
      showMessage('Please wait a few seconds before submitting.', 'error');
      return;
    }

    if (name.length < 2 || name.length > 80) {
      showMessage('Please enter a name between 2 and 80 characters.', 'error');
      return;
    }

    if (comment.length < 5 || comment.length > 2000) {
      showMessage('Please enter a comment between 5 and 2000 characters.', 'error');
      return;
    }

    if (website && !isValidWebsite(website)) {
      showMessage('Website must be a valid http or https URL.', 'error');
      return;
    }

    commentSubmit.disabled = true;
    showMessage('Posting your comment...');

    try {
      var data = await requestJson('POST', 'addComment', {
        visitor_id: getOrCreateVisitorId(),
        name: name,
        website: website,
        comment: comment,
        user_agent: navigator.userAgent || ''
      });

      commentForm.reset();

      if (renderedAtInput) {
        renderedAtInput.value = String(Date.now());
      }

      if (visitorIdInput) {
        visitorIdInput.value = getOrCreateVisitorId();
      }

      updateCounts(data);
      showMessage('Your comment was submitted and is pending approval.', 'success');
    } catch (error) {
      showMessage(error.message || 'Unable to submit comment.', 'error');
    } finally {
      commentSubmit.disabled = false;
    }
  }

  function isValidWebsite(url) {
    try {
      var parsed = new URL(url);
      return parsed.protocol === 'http:' || parsed.protocol === 'https:';
    } catch (error) {
      return false;
    }
  }
})();