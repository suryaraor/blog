var COMMENTS_CONFIG = {
  spreadsheetId: '',
  commentsSheetName: 'comments',
  likesSheetName: 'likes',
  summarySheetName: 'summary',
  newsletterSheetName: 'newsletter',
  likeSaltProperty: 'LIKES_SALT',
  maxCommentsPerWindowPerVisitor: 3,
  rateLimitWindowMinutes: 10,
  duplicateCommentWindowMinutes: 15,
  commentMaxLength: 2000,
  nameMaxLength: 80,
  websiteMaxLength: 200
};

var COMMENTS_HEADERS = {
  comments: ['id', 'post_id', 'page_url', 'name', 'website', 'comment', 'status', 'created_at', 'ip_hash', 'user_agent'],
  likes: ['id', 'post_id', 'page_url', 'visitor_id', 'created_at'],
  summary: ['post_id', 'likes_count', 'approved_comments_count', 'updated_at'],
  newsletter: ['email', 'subscribed_at', 'source_page']
};

function doGet(e) {
  try {
    var action = String((e && e.parameter && e.parameter.action) || 'getPostData');

    if (action === 'getComments') {
      return jsonOutput(getComments(String(e.parameter.post_id || ''), String(e.parameter.page_url || '')));
    }

    if (action === 'getLikes') {
      return jsonOutput(getLikes(String(e.parameter.post_id || ''), String(e.parameter.visitor_id || '')));
    }

    if (action === 'getPostData') {
      return jsonOutput(getPostData({
        post_id: String(e.parameter.post_id || ''),
        page_url: String(e.parameter.page_url || ''),
        visitor_id: String(e.parameter.visitor_id || '')
      }));
    }

    if (action === 'rebuildSummary') {
      return jsonOutput(rebuildSummarySheet());
    }

    return jsonOutput({
      ok: true,
      message: 'Comments service is running.'
    });
  } catch (error) {
    return jsonOutput(errorResponse(error));
  }
}

function doPost(e) {
  try {
    var payload = parsePayload(e);
    var action = String(payload.action || '');

    if (action === 'addComment') {
      return jsonOutput(addComment(payload));
    }

    if (action === 'addLike') {
      return jsonOutput(addLike(payload));
    }

    if (action === 'addNewsletterSubscriber') {
      return jsonOutput(addNewsletterSubscriber(payload));
    }

    return jsonOutput({
      ok: false,
      error: 'Unsupported action.'
    });
  } catch (error) {
    return jsonOutput(errorResponse(error));
  }
}

function jsonOutput(data) {
  return ContentService
    .createTextOutput(JSON.stringify(data))
    .setMimeType(ContentService.MimeType.JSON);
}

function errorResponse(error) {
  return {
    ok: false,
    error: error && error.message ? error.message : String(error)
  };
}

function getPostData(payload) {
  var postId = normalizePostId(payload.post_id);
  var pageUrl = normalizePageUrl(payload.page_url);
  var visitorId = String(payload.visitor_id || '');
  var comments = getComments(postId, pageUrl).comments;
  var likes = getLikes(postId, visitorId);
  var summary = getSummaryRow(postId);

  return {
    ok: true,
    post_id: postId,
    page_url: pageUrl,
    likes_count: likes.likes_count,
    liked: likes.liked,
    approved_comments_count: summary.approved_comments_count,
    comments: comments
  };
}

function getComments(postId, pageUrl) {
  var sheet = getCommentsSheet();
  var rows = readSheetRows(sheet);
  var results = [];

  rows.forEach(function (row) {
    if (normalizePostId(row.post_id) !== postId) {
      return;
    }

    if (pageUrl && normalizePageUrl(row.page_url) !== pageUrl) {
      return;
    }

    if (normalizeStatus(row.status) !== 'approved') {
      return;
    }

    results.push({
      id: row.id,
      post_id: row.post_id,
      page_url: row.page_url,
      name: row.name,
      website: row.website,
      website_label: row.website ? stripProtocol(row.website) : '',
      comment: row.comment,
      status: row.status,
      created_at: row.created_at,
      created_at_iso: normalizeDateIso(row.created_at)
    });
  });

  return {
    ok: true,
    post_id: postId,
    page_url: pageUrl,
    comments: results
  };
}

function getLikes(postId, visitorId) {
  var sheet = getLikesSheet();
  var rows = readSheetRows(sheet);
  var count = 0;
  var liked = false;

  rows.forEach(function (row) {
    if (normalizePostId(row.post_id) !== postId) {
      return;
    }

    count += 1;

    if (visitorId && String(row.visitor_id || '') === visitorId) {
      liked = true;
    }
  });

  return {
    ok: true,
    post_id: postId,
    likes_count: count,
    liked: liked
  };
}

function addComment(payload) {
  var lock = LockService.getScriptLock();
  lock.waitLock(30000);

  try {
    var postId = normalizePostId(payload.post_id);
    var pageUrl = normalizePageUrl(payload.page_url);
    var visitorId = String(payload.visitor_id || '');
    var name = sanitizeInput(payload.name, COMMENTS_CONFIG.nameMaxLength, false);
    var website = sanitizeWebsite(payload.website, COMMENTS_CONFIG.websiteMaxLength);
    var comment = sanitizeInput(payload.comment, COMMENTS_CONFIG.commentMaxLength, true);
    var userAgent = sanitizeInput(payload.user_agent, 300, false);

    validateCommentInput(postId, pageUrl, name, comment);
    rateLimitComment(postId, visitorId);
    rejectDuplicateComment(postId, visitorId, name, comment);

    var sheet = getCommentsSheet();
    var timestamp = new Date();
    var id = Utilities.getUuid();
    var visitorHash = hashString([visitorId, postId, getLikeSalt()].join('|'));

    sheet.appendRow([
      id,
      postId,
      pageUrl,
      name,
      website,
      comment,
      'approved',
      timestamp,
      visitorHash,
      userAgent
    ]);

    updateSummaryRow(postId);

    return {
      ok: true,
      message: 'Comment posted.',
      status: 'approved',
      approved_comments_count: getSummaryRow(postId).approved_comments_count,
      likes_count: getLikes(postId, visitorId).likes_count
    };
  } finally {
    lock.releaseLock();
  }
}

function addLike(payload) {
  var lock = LockService.getScriptLock();
  lock.waitLock(30000);

  try {
    var postId = normalizePostId(payload.post_id);
    var pageUrl = normalizePageUrl(payload.page_url);
    var visitorId = String(payload.visitor_id || '');

    validateLikeInput(postId, visitorId);

    var sheet = getLikesSheet();
    var rows = readSheetRows(sheet);
    var alreadyLiked = rows.some(function (row) {
      return normalizePostId(row.post_id) === postId && String(row.visitor_id || '') === visitorId;
    });

    if (!alreadyLiked) {
      sheet.appendRow([
        Utilities.getUuid(),
        postId,
        pageUrl,
        visitorId,
        new Date()
      ]);
    }

    updateSummaryRow(postId);

    return {
      ok: true,
      message: alreadyLiked ? 'Like already recorded.' : 'Like recorded.',
      liked: true,
      likes_count: getLikes(postId, visitorId).likes_count
    };
  } finally {
    lock.releaseLock();
  }
}

function addNewsletterSubscriber(payload) {
  var lock = LockService.getScriptLock();
  lock.waitLock(30000);

  try {
    var email = sanitizeInput(payload.email, 320, false).toLowerCase();
    var sourcePage = sanitizeInput(payload.source_page, 500, false);

    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      throw new Error('Invalid email address.');
    }

    var sheet = getNewsletterSheet();
    var rows = readSheetRows(sheet);
    var alreadySubscribed = rows.some(function (row) {
      return String(row.email || '').toLowerCase().trim() === email;
    });

    if (!alreadySubscribed) {
      sheet.appendRow([email, new Date(), sourcePage]);
    }

    return {
      ok: true,
      message: alreadySubscribed ? 'Already subscribed.' : 'Subscribed successfully.'
    };
  } finally {
    lock.releaseLock();
  }
}

function getNewsletterSheet() {
  return getOrCreateSheet(COMMENTS_CONFIG.newsletterSheetName, COMMENTS_HEADERS.newsletter);
}

function sanitizeInput(value, maxLength, allowNewlines) {
  var text = value === undefined || value === null ? '' : String(value);
  text = text.replace(/\u0000/g, '').trim();
  text = text.replace(/[\u200B-\u200D\uFEFF]/g, '');

  if (!allowNewlines) {
    text = text.replace(/[\r\n\t]+/g, ' ');
  }

  text = text.replace(/\s{2,}/g, ' ');

  if (text.length > maxLength) {
    text = text.slice(0, maxLength);
  }

  return text;
}

function sanitizeWebsite(value, maxLength) {
  var website = sanitizeInput(value, maxLength, false);

  if (!website) {
    return '';
  }

  if (!/^https?:\/\//i.test(website)) {
    website = 'https://' + website;
  }

  try {
    var parsed = new URL(website);
    return parsed.protocol === 'http:' || parsed.protocol === 'https:' ? parsed.toString() : '';
  } catch (error) {
    return '';
  }
}

function validateCommentInput(postId, pageUrl, name, comment) {
  if (!postId) {
    throw new Error('Missing post_id.');
  }

  if (!pageUrl) {
    throw new Error('Missing page_url.');
  }

  if (name.length < 2 || name.length > COMMENTS_CONFIG.nameMaxLength) {
    throw new Error('Name must be between 2 and ' + COMMENTS_CONFIG.nameMaxLength + ' characters.');
  }

  if (comment.length < 5 || comment.length > COMMENTS_CONFIG.commentMaxLength) {
    throw new Error('Comment must be between 5 and ' + COMMENTS_CONFIG.commentMaxLength + ' characters.');
  }

}

function validateLikeInput(postId, visitorId) {
  if (!postId) {
    throw new Error('Missing post_id.');
  }

  if (!visitorId) {
    throw new Error('Missing visitor_id.');
  }
}

function rateLimitComment(postId, visitorId) {
  if (!visitorId) {
    return;
  }

  var sheet = getCommentsSheet();
  var rows = readSheetRows(sheet);
  var now = Date.now();
  var windowMinutes = COMMENTS_CONFIG.rateLimitWindowMinutes;
  var maxComments = COMMENTS_CONFIG.maxCommentsPerWindowPerVisitor;
  var cutoff = now - windowMinutes * 60 * 1000;
  var count = 0;

  rows.forEach(function (row) {
    if (normalizePostId(row.post_id) !== postId) {
      return;
    }

    if (String(row.ip_hash || '') !== hashString([visitorId, postId, getLikeSalt()].join('|'))) {
      return;
    }

    var rowTime = new Date(row.created_at).getTime();
    if (!isNaN(rowTime) && rowTime >= cutoff) {
      count += 1;
    }
  });

  if (count >= maxComments) {
    throw new Error('Too many comments in a short period. Please slow down.');
  }
}

function rejectDuplicateComment(postId, visitorId, name, comment) {
  if (!visitorId) {
    return;
  }

  var sheet = getCommentsSheet();
  var rows = readSheetRows(sheet);
  var targetHash = hashString([visitorId, postId, getLikeSalt()].join('|'));
  var duplicateHash = hashString([postId, name.toLowerCase(), comment.toLowerCase()].join('|'));
  var cutoff = Date.now() - COMMENTS_CONFIG.duplicateCommentWindowMinutes * 60 * 1000;

  rows.forEach(function (row) {
    if (normalizePostId(row.post_id) !== postId) {
      return;
    }

    var rowTime = new Date(row.created_at).getTime();
    if (!isNaN(rowTime) && rowTime < cutoff) {
      return;
    }

    if (String(row.ip_hash || '') === targetHash) {
      if (hashString([postId, String(row.name || '').toLowerCase(), String(row.comment || '').toLowerCase()].join('|')) === duplicateHash) {
        throw new Error('Duplicate comment detected. Please edit your message before submitting again.');
      }
    }
  });
}

function getSummaryRow(postId) {
  var sheet = getSummarySheet();
  var rows = readSheetRows(sheet);
  var match = rows.filter(function (row) {
    return normalizePostId(row.post_id) === postId;
  })[0];

  if (!match) {
    return {
      post_id: postId,
      likes_count: 0,
      approved_comments_count: 0,
      updated_at: ''
    };
  }

  return {
    post_id: match.post_id,
    likes_count: Number(match.likes_count || 0),
    approved_comments_count: Number(match.approved_comments_count || 0),
    updated_at: match.updated_at
  };
}

function updateSummaryRow(postId) {
  var commentsSheet = getCommentsSheet();
  var likesSheet = getLikesSheet();
  var summarySheet = getSummarySheet();
  var comments = readSheetRows(commentsSheet);
  var likes = readSheetRows(likesSheet);
  var approvedCommentsCount = comments.filter(function (row) {
    return normalizePostId(row.post_id) === postId && normalizeStatus(row.status) === 'approved';
  }).length;
  var likesCount = likes.filter(function (row) {
    return normalizePostId(row.post_id) === postId;
  }).length;
  var rows = readSheetRows(summarySheet);
  var rowIndex = -1;

  for (var i = 0; i < rows.length; i += 1) {
    if (normalizePostId(rows[i].post_id) === postId) {
      rowIndex = i + 2;
      break;
    }
  }

  var values = [postId, likesCount, approvedCommentsCount, new Date()];

  if (rowIndex === -1) {
    summarySheet.appendRow(values);
  } else {
    summarySheet.getRange(rowIndex, 1, 1, values.length).setValues([values]);
  }

  return {
    post_id: postId,
    likes_count: likesCount,
    approved_comments_count: approvedCommentsCount,
    updated_at: new Date().toISOString()
  };
}

function rebuildSummarySheet() {
  var comments = readSheetRows(getCommentsSheet());
  var likes = readSheetRows(getLikesSheet());
  var summarySheet = getSummarySheet();
  var aggregate = {};

  comments.forEach(function (row) {
    var key = normalizePostId(row.post_id);
    if (!key) {
      return;
    }

    if (!aggregate[key]) {
      aggregate[key] = { likes_count: 0, approved_comments_count: 0 };
    }

    if (normalizeStatus(row.status) === 'approved') {
      aggregate[key].approved_comments_count += 1;
    }
  });

  likes.forEach(function (row) {
    var key = normalizePostId(row.post_id);
    if (!key) {
      return;
    }

    if (!aggregate[key]) {
      aggregate[key] = { likes_count: 0, approved_comments_count: 0 };
    }

    aggregate[key].likes_count += 1;
  });

  summarySheet.clearContents();
  ensureHeaders(summarySheet, COMMENTS_HEADERS.summary);

  Object.keys(aggregate).sort().forEach(function (postId) {
    var entry = aggregate[postId];
    summarySheet.appendRow([
      postId,
      entry.likes_count,
      entry.approved_comments_count,
      new Date()
    ]);
  });

  return {
    ok: true,
    summary_rows: Object.keys(aggregate).length
  };
}

function createDailyMaintenanceTrigger() {
  deleteExistingTriggers('dailyMaintenance');
  ScriptApp.newTrigger('dailyMaintenance').timeBased().everyDays(1).atHour(3).create();
}

function dailyMaintenance() {
  rebuildSummarySheet();
}

function deleteExistingTriggers(handlerName) {
  ScriptApp.getProjectTriggers().forEach(function (trigger) {
    if (trigger.getHandlerFunction() === handlerName) {
      ScriptApp.deleteTrigger(trigger);
    }
  });
}

function parsePayload(e) {
  if (!e || !e.postData) {
    return e && e.parameter ? e.parameter : {};
  }

  var contents = String(e.postData.contents || '').trim();
  var contentType = String(e.postData.type || '').toLowerCase();

  if (!contents) {
    return e.parameter || {};
  }

  if (contentType.indexOf('application/json') !== -1) {
    return JSON.parse(contents);
  }

  if (contentType.indexOf('application/x-www-form-urlencoded') !== -1 || contents.indexOf('=') !== -1) {
    return contents.split('&').reduce(function (acc, pair) {
      var parts = pair.split('=');
      var key = decodeURIComponent((parts[0] || '').replace(/\+/g, '%20'));
      var value = decodeURIComponent((parts[1] || '').replace(/\+/g, '%20'));
      if (key) {
        acc[key] = value;
      }
      return acc;
    }, {});
  }

  return e.parameter || {};
}

function getCommentsSheet() {
  return getOrCreateSheet(COMMENTS_CONFIG.commentsSheetName, COMMENTS_HEADERS.comments);
}

function getLikesSheet() {
  return getOrCreateSheet(COMMENTS_CONFIG.likesSheetName, COMMENTS_HEADERS.likes);
}

function getSummarySheet() {
  return getOrCreateSheet(COMMENTS_CONFIG.summarySheetName, COMMENTS_HEADERS.summary);
}

function getOrCreateSheet(sheetName, headers) {
  var spreadsheet = getSpreadsheet();
  var sheet = spreadsheet.getSheetByName(sheetName);

  if (!sheet) {
    sheet = spreadsheet.insertSheet(sheetName);
  }

  ensureHeaders(sheet, headers);
  return sheet;
}

function ensureHeaders(sheet, headers) {
  var firstRow = sheet.getRange(1, 1, 1, headers.length).getValues()[0];
  var hasHeaders = headers.every(function (header, index) {
    return String(firstRow[index] || '') === header;
  });

  if (!hasHeaders) {
    sheet.clearContents();
    sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
  }
}

function readSheetRows(sheet) {
  var lastRow = sheet.getLastRow();
  var lastColumn = sheet.getLastColumn();

  if (lastRow < 2 || lastColumn < 1) {
    return [];
  }

  var values = sheet.getRange(2, 1, lastRow - 1, lastColumn).getValues();
  var headers = sheet.getRange(1, 1, 1, lastColumn).getValues()[0];

  return values.map(function (row) {
    var item = {};

    headers.forEach(function (header, index) {
      item[String(header || '').trim()] = row[index];
    });

    return item;
  });
}

function getSpreadsheet() {
  var spreadsheetId = getConfig().spreadsheetId;

  if (!spreadsheetId) {
    throw new Error('Missing SPREADSHEET_ID script property.');
  }

  return SpreadsheetApp.openById(spreadsheetId);
}

function getConfig() {
  var properties = PropertiesService.getScriptProperties();
  return {
    spreadsheetId: properties.getProperty('SPREADSHEET_ID') || COMMENTS_CONFIG.spreadsheetId
  };
}

function getLikeSalt() {
  var properties = PropertiesService.getScriptProperties();
  return properties.getProperty(COMMENTS_CONFIG.likeSaltProperty) || 'change-me';
}

function normalizePostId(value) {
  return String(value || '').trim();
}

function normalizePageUrl(value) {
  return String(value || '').trim();
}

function normalizeStatus(value) {
  return String(value || '').toLowerCase().trim();
}

function normalizeDateIso(value) {
  var date = new Date(value);
  if (isNaN(date.getTime())) {
    return '';
  }

  return date.toISOString();
}

function stripProtocol(url) {
  return String(url || '').replace(/^https?:\/\//i, '').replace(/\/+$/, '');
}

function hashString(value) {
  var bytes = Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, value, Utilities.Charset.UTF_8);
  return bytes.map(function (byte) {
    var unsigned = byte < 0 ? byte + 256 : byte;
    return ('0' + unsigned.toString(16)).slice(-2);
  }).join('');
}