(function () {
  var panel = document.getElementById("wa-messages-panel");
  var form = document.getElementById("wa-message-form");
  var errEl = document.getElementById("wa-compose-error");
  var cfgEl = document.getElementById("wa-chat-config");
  var cfg = {};
  try {
    cfg = cfgEl && cfgEl.textContent ? JSON.parse(cfgEl.textContent) : {};
  } catch (e) {}
  function normalizedSendUrl() {
    var fromForm = form ? form.getAttribute("action") || "" : "";
    var u = fromForm || cfg.sendUrl || "";
    /* APPEND_SLASH safety for POST endpoints */
    if (u && u.indexOf("?") === -1 && u.slice(-1) !== "/") u += "/";
    return u;
  }

  function showErr(msg) {
    if (!errEl) return;
    errEl.textContent = msg || "";
    errEl.classList.toggle("hidden", !msg);
  }

  function getCsrfToken() {
    var inp = document.querySelector("#wa-message-form [name=csrfmiddlewaretoken]");
    if (inp && inp.value) return inp.value;
    var m = document.cookie.match(/csrftoken=([^;]+)/);
    return m ? decodeURIComponent(m[1].trim()) : "";
  }

  var seenIds = new Set();
  if (panel) {
    panel.querySelectorAll("[data-msg-id]").forEach(function (el) {
      var id = el.getAttribute("data-msg-id");
      if (id) seenIds.add(parseInt(id, 10));
    });
  }

  function appendBubble(m) {
    var mid = m.id;
    if (mid != null) {
      var n = typeof mid === "number" ? mid : parseInt(mid, 10);
      if (!isNaN(n)) {
        if (seenIds.has(n)) return;
        seenIds.add(n);
      }
    }
    if (!panel) return;

    var mine = m.sender_id === (window.WA_USER_ID || 0);
    var wrap = document.createElement("div");
    wrap.className = "wa-msg-row mb-1 flex " + (mine ? "wa-msg-mine justify-end" : "");
    if (mid != null) wrap.setAttribute("data-msg-id", String(mid));

    var bubble = document.createElement("div");
    bubble.className = "wa-bubble";
    var mt = (m.type != null ? String(m.type) : "").toLowerCase();
    if (mt === "text") {
      var t = document.createElement("div");
      t.className = "text-sm text-foreground whitespace-pre-wrap break-words";
      t.textContent = m.body || "";
      bubble.appendChild(t);
    } else if (mt === "image" && (m.image_url || m.file_url)) {
      var srcImg = m.image_url || m.file_url;
      var a = document.createElement("a");
      a.href = srcImg;
      a.target = "_blank";
      a.rel = "noopener";
      var img = document.createElement("img");
      img.className = "max-h-64 max-w-[min(100%,280px)] rounded-md";
      img.src = srcImg;
      img.alt = "";
      a.appendChild(img);
      bubble.appendChild(a);
      if (m.body) {
        var cap = document.createElement("p");
        cap.className = "mt-1 text-sm text-foreground";
        cap.textContent = m.body;
        bubble.appendChild(cap);
      }
    } else if (mt === "file" && m.file_url) {
      var url = m.file_url;
      var looksImg =
        /\.(jpe?g|png|gif|webp|bmp|tif|tiff|heic|heif)(\?|#|$)/i.test(url) ||
        /\.(jpe?g|png|gif|webp|bmp|tif|tiff|heic|heif)$/i.test(m.file_name || "");
      if (looksImg) {
        var a2 = document.createElement("a");
        a2.href = url;
        a2.target = "_blank";
        a2.rel = "noopener";
        var img2 = document.createElement("img");
        img2.className = "max-h-64 max-w-[min(100%,280px)] rounded-md";
        img2.src = url;
        img2.alt = "";
        a2.appendChild(img2);
        bubble.appendChild(a2);
        if (m.body) {
          var cap2 = document.createElement("p");
          cap2.className = "mt-1 text-sm text-foreground";
          cap2.textContent = m.body;
          bubble.appendChild(cap2);
        }
      } else {
        var fl = document.createElement("a");
        fl.className = "text-sm text-primary underline break-all";
        fl.href = m.file_url;
        fl.target = "_blank";
        fl.rel = "noopener";
        fl.textContent = m.file_name || "File";
        bubble.appendChild(fl);
      }
    } else if (mt === "voice" && m.voice_url) {
      var aud = document.createElement("audio");
      aud.className = "h-9 max-w-[260px]";
      aud.controls = true;
      aud.src = m.voice_url;
      bubble.appendChild(aud);
    } else {
      var fb = document.createElement("div");
      fb.className = "text-sm text-foreground";
      fb.textContent = m.body || "";
      bubble.appendChild(fb);
    }
    var meta = document.createElement("div");
    meta.className = "mt-0.5 text-right text-[10px] text-muted-foreground";
    meta.textContent = m.created
      ? new Date(m.created).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })
      : "";
    bubble.appendChild(meta);
    wrap.appendChild(bubble);
    panel.appendChild(wrap);
    panel.scrollTop = panel.scrollHeight;
  }

  function connectWs() {
    if (!window.WebSocket) return;
    var wsUrl = cfg.wsUrl;
    if (!wsUrl && cfg.wsPath) {
      var proto = window.location.protocol === "https:" ? "wss" : "ws";
      wsUrl = proto + "://" + window.location.host + cfg.wsPath;
    }
    if (!wsUrl && cfg.roomId) {
      var proto2 = window.location.protocol === "https:" ? "wss" : "ws";
      wsUrl = proto2 + "://" + window.location.host + "/ws/chat/" + cfg.roomId + "/";
    }
    if (!wsUrl) return;
    var socket = new WebSocket(wsUrl);
    socket.onmessage = function (ev) {
      try {
        var data = JSON.parse(ev.data);
        if (data.event === "new_message" && data.message) {
          appendBubble(data.message);
        }
      } catch (err) {}
    };
    socket.onclose = function () {
      window.setTimeout(connectWs, 3000);
    };
    socket.onerror = function () {
      showErr("Realtime connection interrupted. Messages still send via HTTP.");
    };
  }
  connectWs();

  /** ---- Voice recording (MediaRecorder) ---- */
  var mediaRecorder = null;
  var recordChunks = [];
  var recordStream = null;
  var micBtn = document.getElementById("wa-mic-btn");

  function stopStream() {
    if (recordStream) {
      recordStream.getTracks().forEach(function (t) {
        t.stop();
      });
      recordStream = null;
    }
  }

  if (micBtn) {
    micBtn.addEventListener("click", function () {
      showErr("");
      if (mediaRecorder && mediaRecorder.state === "recording") {
        mediaRecorder.stop();
        return;
      }
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        showErr("Microphone not supported in this browser.");
        return;
      }
      navigator.mediaDevices
        .getUserMedia({ audio: true })
        .then(function (stream) {
          recordStream = stream;
          recordChunks = [];
          var mime = "audio/webm";
          if (MediaRecorder.isTypeSupported("audio/webm;codecs=opus")) {
            mime = "audio/webm;codecs=opus";
          } else if (MediaRecorder.isTypeSupported("audio/mp4")) {
            mime = "audio/mp4";
          }
          try {
            mediaRecorder = new MediaRecorder(stream, { mimeType: mime });
          } catch (e) {
            mediaRecorder = new MediaRecorder(stream);
          }
          mediaRecorder.ondataavailable = function (e) {
            if (e.data && e.data.size) recordChunks.push(e.data);
          };
          mediaRecorder.onstop = function () {
            stopStream();
            mediaRecorder = null;
            var blob = new Blob(recordChunks, { type: mime.split(";")[0] || "audio/webm" });
            recordChunks = [];
            if (!blob.size) {
              showErr("Recording was empty.");
              micBtn.classList.remove("bg-destructive/20", "text-destructive");
              return;
            }
            var ext = blob.type.indexOf("mp4") >= 0 ? "m4a" : "webm";
            sendWithFiles({ voiceBlob: blob, voiceName: "voice." + ext });
            micBtn.classList.remove("bg-destructive/20", "text-destructive");
          };
          mediaRecorder.start();
          micBtn.classList.add("bg-destructive/20", "text-destructive");
        })
        .catch(function (err) {
          showErr("Microphone: " + (err.message || "permission denied"));
        });
    });
  }

  function sendWithFiles(extra) {
    var sendUrl = normalizedSendUrl();
    if (!form || !sendUrl) {
      showErr("Cannot send — reload the page.");
      return;
    }
    showErr("");
    var fd = new FormData(form);
    if (extra && extra.voiceBlob) {
      fd.delete("voice");
      fd.append("voice", extra.voiceBlob, extra.voiceName || "voice.webm");
    }
    var token = getCsrfToken();
    if (!token) {
      showErr("Security token missing — refresh the page and try again.");
      return;
    }
    fetch(sendUrl, {
      method: "POST",
      headers: {
        "X-Requested-With": "XMLHttpRequest",
        "X-CSRFToken": token,
        Accept: "application/json",
      },
      body: fd,
      credentials: "same-origin",
    })
      .then(function (r) {
        return r.text().then(function (text) {
          var data = {};
          try {
            data = text ? JSON.parse(text) : {};
          } catch (e) {
            if (!r.ok) throw new Error("Server error (" + r.status + ")");
          }
          return { ok: r.ok, status: r.status, data: data };
        });
      })
      .then(function (res) {
        if (!res.ok || !res.data.ok) {
          var msg = "Send failed.";
          if (res.data && typeof res.data.error === "string" && res.data.error) {
            msg = res.data.error;
          } else if (res.data && typeof res.data.detail === "string" && res.data.detail) {
            msg = res.data.detail;
          } else if (res.data && res.data.errors) {
            msg = "Validation failed.";
          } else {
            msg = "HTTP " + res.status;
          }
          if (res.data && res.data.errors) {
            try {
              var asObj = res.data.errors;
              var keys = Object.keys(asObj || {});
              if (keys.length) {
                var first = keys[0];
                var firstErr = (asObj[first] && asObj[first][0] && asObj[first][0].message) || "";
                if (firstErr) msg = first + ": " + firstErr;
              }
            } catch (e) {}
          }
          showErr(typeof msg === "string" ? msg : "Send failed.");
          return;
        }
        if (res.data.message) appendBubble(res.data.message);
        form.reset();
        var inp = form.querySelector("textarea[name=body]");
        if (inp) inp.style.height = "auto";
      })
      .catch(function (err) {
        showErr(err && err.message ? err.message : "Network error — try again.");
      });
  }

  if (!form) return;

  function hasAttachmentInFormData(fd) {
    if (!fd) return false;
    var keys = ["image", "file", "voice"];
    for (var i = 0; i < keys.length; i++) {
      var v = fd.get(keys[i]);
      if (v && typeof v === "object" && typeof v.size === "number" && v.size > 0) {
        return true;
      }
    }
    return false;
  }

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    var fd = new FormData(form);
    var text = (fd.get("body") || "").toString().trim();
    var hasFile = hasAttachmentInFormData(fd);
    if (!text && !hasFile) {
      showErr("Type a message or attach a file.");
      return;
    }
    if (!normalizedSendUrl() || !window.fetch) {
      form.submit();
      return;
    }
    sendWithFiles(null);
  });

  if (panel) panel.scrollTop = panel.scrollHeight;

  ["image", "file", "voice"].forEach(function (name) {
    var input = form ? form.querySelector('[name="' + name + '"]') : null;
    if (!input) return;
    input.addEventListener("change", function () {
      var f = input.files && input.files[0];
      if (!f) return;
      showErr("Attached: " + f.name + " (" + Math.ceil(f.size / 1024) + " KB)");
      /* Auto-send attachment immediately after selection */
      if (window.fetch && normalizedSendUrl()) {
        sendWithFiles(null);
      } else {
        form.submit();
      }
    });
  });
})();
