(function () {
  'use strict';

  var root = document.querySelector('.post-comments');
  if (!root) return;

  var apiUrl = (root.dataset.apiUrl || '').replace(/\/+$/, '');
  var postId = root.dataset.postId || window.location.pathname;
  var commentList = root.querySelector('[data-comment-list]');
  var commentForm = root.querySelector('[data-comment-form]');
  var commentSubmit = root.querySelector('[data-comment-submit]');
  var statusEl = root.querySelector('[data-status]');

  if (!apiUrl) return;

  loadComments();

  if (commentForm) {
    commentForm.addEventListener('submit', handleSubmit);
  }

  function loadComments(showLoading) {
    if (showLoading && commentList) {
      var loadingLi = document.createElement('li');
      loadingLi.className = 'comment-list__loading';
      loadingLi.textContent = 'Loading comments…';
      commentList.innerHTML = '';
      commentList.appendChild(loadingLi);
    }
    var url = apiUrl + '?action=getComments&post_id=' + encodeURIComponent(postId) + '&_=' + Date.now();
    fetch(url, { mode: 'cors', credentials: 'omit', cache: 'no-store' })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        renderComments(data.comments || []);
        if (showLoading && commentList) {
          commentList.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
      })
      .catch(function () {
        if (showLoading && commentList) commentList.innerHTML = '';
      });
  }

  function renderComments(comments) {
    if (!commentList) return;
    commentList.innerHTML = '';
    comments.forEach(function (c) {
      if (!c || !c.comment) return;
      var li = document.createElement('li');
      li.className = 'comment-card';
      li.innerHTML =
        '<div class="comment-card__meta">' +
          '<span class="comment-card__name">' + escapeHtml(c.name || 'Anonymous') + '</span>' +
          '<time>' + formatDate(c.created_at || c.created_at_iso) + '</time>' +
        '</div>' +
        '<p class="comment-card__body">' + escapeHtml(c.comment) + '</p>';
      commentList.appendChild(li);
    });
  }

  async function handleSubmit(e) {
    e.preventDefault();
    var formData = new FormData(commentForm);

    if ((formData.get('company') || '').trim()) return;

    var name = (formData.get('name') || '').trim();
    var comment = (formData.get('comment') || '').trim();

    if (name.length < 2) return setStatus('Please enter your name.');
    if (comment.length < 5) return setStatus('Comment is too short.');

    setSubmitting(true);
    setStatus('');

    var body = new URLSearchParams({
      action: 'addComment',
      post_id: postId,
      page_url: formData.get('page_url') || window.location.pathname,
      post_title: formData.get('post_title') || document.title,
      name: name,
      comment: comment,
      _: String(Date.now())
    });

    try {
      var r = await fetch(apiUrl, {
        method: 'POST',
        mode: 'cors',
        credentials: 'omit',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8' },
        body: body.toString()
      });
      var data = await r.json();
      if (data.ok === false) throw new Error(data.error || 'Failed to post comment.');
      commentForm.reset();
      setStatus('Comment posted!');
      loadComments(true);
    } catch (err) {
      setStatus(err.message || 'Unable to post comment. Please try again.');
    } finally {
      setSubmitting(false);
    }
  }

  function setSubmitting(on) {
    commentSubmit.disabled = on;
    commentSubmit.innerHTML = on
      ? '<span class="btn-spinner" aria-hidden="true"></span>Posting…'
      : 'Post comment';
  }

  function setStatus(msg) {
    if (statusEl) statusEl.textContent = msg;
  }

  function escapeHtml(str) {
    return String(str || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function formatDate(value) {
    if (!value) return '';
    var d = new Date(value);
    if (isNaN(d.getTime())) return String(value);
    return new Intl.DateTimeFormat(undefined, { year: 'numeric', month: 'short', day: 'numeric' }).format(d);
  }
})();
