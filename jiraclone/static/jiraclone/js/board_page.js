(function () {
  function getCookie(name) {
    var v = document.cookie.match("(^|;)\\s*" + name + "\\s*=\\s*([^;]+)");
    return v ? v.pop() : "";
  }

  function qs(sel, root) {
    return (root || document).querySelector(sel);
  }
  function qsa(sel, root) {
    return Array.prototype.slice.call((root || document).querySelectorAll(sel));
  }

  var root = qs("#jira-board-root");
  if (!root) return;

  var projectKey = root.getAttribute("data-project-key") || "";
  var canManage = root.getAttribute("data-can-manage") === "true";
  var apiBase = (root.getAttribute("data-api-base") || "/api/jiraclone").replace(/\/$/, "");
  var csrf = getCookie("csrftoken");

  var sj = document.getElementById("jira-statuses-json");
  if (sj) {
    try {
      window.__jiraStatuses = JSON.parse(sj.textContent);
    } catch (e) {
      window.__jiraStatuses = [];
    }
  }

  function apiUrl(path) {
    return apiBase + path;
  }

  function postJson(url, body) {
    return fetch(url, {
      method: "POST",
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrf,
      },
      body: JSON.stringify(body),
    }).then(function (r) {
      return r.json().then(function (data) {
        return { ok: r.ok, status: r.status, data: data };
      });
    });
  }

  function getJson(url) {
    return fetch(url, { credentials: "same-origin", headers: { Accept: "application/json" } }).then(function (r) {
      return r.json().then(function (data) {
        return { ok: r.ok, data: data };
      });
    });
  }

  function escHtml(s) {
    var d = document.createElement("div");
    d.textContent = s == null ? "" : String(s);
    return d.innerHTML;
  }

  var drawer = qs("#jira-issue-drawer");
  var drawerBackdrop = qs("#jira-drawer-backdrop");
  var drawerBody = qs("#jira-drawer-body");
  var drawerTitle = qs("#jira-drawer-title");
  var btnCloseDrawer = qs("#jira-drawer-close");

  function closeDrawer() {
    if (!drawer) return;
    drawer.classList.add("hidden");
    drawer.setAttribute("aria-hidden", "true");
    if (drawerBackdrop) drawerBackdrop.classList.add("hidden");
    document.body.classList.remove("overflow-hidden");
  }

  function openDrawer() {
    if (!drawer) return;
    drawer.classList.remove("hidden");
    drawer.setAttribute("aria-hidden", "false");
    if (drawerBackdrop) drawerBackdrop.classList.remove("hidden");
    document.body.classList.add("overflow-hidden");
  }

  if (btnCloseDrawer) btnCloseDrawer.addEventListener("click", closeDrawer);
  if (drawerBackdrop) drawerBackdrop.addEventListener("click", closeDrawer);

  function renderIssue(issue) {
    if (!issue || !drawerBody) return;
    var lines = [];
    var it = issue.issue_type || {};
    var st = issue.status || {};
    lines.push('<div class="space-y-4 text-sm">');
    lines.push('<div class="flex flex-wrap gap-2 text-xs">');
    lines.push('<span class="rounded-full bg-muted px-2 py-0.5">' + escHtml(it.name || "") + "</span>");
    lines.push('<span class="rounded-full bg-muted px-2 py-0.5">' + escHtml(st.name || "") + "</span>");
    lines.push(
      '<span class="rounded-full bg-muted px-2 py-0.5">' + escHtml(issue.priority_display || "") + "</span>"
    );
    lines.push("</div>");
    lines.push('<div><h3 class="text-xs font-semibold uppercase text-muted-foreground">Description</h3>');
    lines.push(
      '<p class="mt-1 whitespace-pre-wrap text-foreground">' +
        (issue.description ? escHtml(issue.description) : "—") +
        "</p></div>"
    );

    if (issue.can_manage) {
      var dueVal = issue.due_date ? String(issue.due_date).slice(0, 10) : "";
      lines.push('<div class="rounded-lg border border-border p-3 space-y-2">');
      lines.push('<p class="text-xs font-semibold uppercase text-muted-foreground">Due date &amp; assignees</p>');
      if (issue.teams_configured === false) {
        lines.push(
          '<p class="text-[11px] text-muted-foreground">No teams yet — any workspace user can be assigned. Add <a href="/dashboard/jiraclone/project/' +
            encodeURIComponent(projectKey) +
            '/teams/" class="text-primary underline">Teams</a> to restrict like Jira.</p>'
        );
      }
      lines.push('<label class="text-xs text-muted-foreground">Due date</label>');
      lines.push(
        '<input type="date" id="jira-due-date" class="inv-list-control w-full text-sm" value="' +
          escHtml(dueVal) +
          '" />'
      );
      lines.push(
        '<label class="text-xs text-muted-foreground">Assignees (hold Ctrl/Cmd to pick several)</label>'
      );
      lines.push('<select id="jira-assignees" multiple class="inv-list-control w-full min-h-[120px]" size="6">');
      var selIds = {};
      (issue.assignees || []).forEach(function (u) {
        selIds[u.id] = true;
      });
      (issue.assignable_users || []).forEach(function (u) {
        lines.push(
          '<option value="' +
            u.id +
            '"' +
            (selIds[u.id] ? " selected" : "") +
            ">" +
            escHtml(u.name) +
            "</option>"
        );
      });
      lines.push("</select>");
      lines.push(
        '<button type="button" id="jira-fields-save" class="rounded-lg bg-primary px-3 py-2 text-xs font-medium text-primary-foreground">Save due date &amp; assignees</button>'
      );
      lines.push("</div>");
    }

    if (issue.can_manage && st.id) {
      lines.push('<div class="rounded-lg border border-border p-2">');
      lines.push('<label class="text-xs text-muted-foreground">Status</label>');
      lines.push(
        '<select id="jira-drawer-status" class="inv-list-control mt-1 w-full text-sm" data-issue-id="' +
          issue.id +
          '">'
      );
      (window.__jiraStatuses || []).forEach(function (row) {
        lines.push(
          '<option value="' +
            row.id +
            '"' +
            (row.id === st.id ? " selected" : "") +
            ">" +
            escHtml(row.name) +
            "</option>"
        );
      });
      lines.push("</select></div>");
    }

    if (!issue.can_manage) {
      lines.push('<div><h3 class="text-xs font-semibold uppercase text-muted-foreground">Assignees</h3>');
      if (issue.assignees && issue.assignees.length) {
        lines.push('<ul class="mt-1 list-inside list-disc">');
        issue.assignees.forEach(function (u) {
          lines.push("<li>" + escHtml(u.name) + "</li>");
        });
        lines.push("</ul>");
      } else {
        lines.push('<p class="mt-1 text-muted-foreground">Unassigned</p>');
      }
      lines.push("</div>");
    }

    lines.push('<div><h3 class="text-xs font-semibold uppercase text-muted-foreground">Subtasks</h3>');
    if (issue.subtasks && issue.subtasks.length) {
      lines.push('<ul class="mt-2 space-y-1">');
      issue.subtasks.forEach(function (sub) {
        lines.push(
          '<li class="flex flex-wrap gap-2"><button type="button" class="jira-open-sub font-mono text-xs text-primary hover:underline" data-id="' +
            sub.id +
            '">' +
            escHtml(sub.issue_key) +
            "</button><span>" +
            escHtml(sub.summary) +
            "</span></li>"
        );
      });
      lines.push("</ul>");
    } else {
      lines.push('<p class="mt-1 text-muted-foreground">None</p>');
    }
    lines.push("</div>");

    if (canManage && !issue.parent_id) {
      lines.push('<div class="rounded-lg border border-dashed border-border p-3">');
      lines.push('<label class="text-xs font-medium text-muted-foreground">New subtask</label>');
      lines.push(
        '<div class="mt-2 flex gap-2"><input type="text" id="jira-subtask-summary" class="inv-list-control flex-1 text-sm" placeholder="Summary" />'
      );
      lines.push(
        '<button type="button" id="jira-subtask-btn" class="rounded-lg bg-primary px-3 py-2 text-xs font-medium text-primary-foreground" data-parent="' +
          issue.id +
          '">Add</button></div></div>'
      );
    }

    lines.push('<div><h3 class="text-xs font-semibold uppercase text-muted-foreground">Activity</h3>');
    if (issue.comments && issue.comments.length) {
      issue.comments.forEach(function (c) {
        lines.push(
          '<div class="mt-2 rounded-lg border border-border bg-muted/20 px-3 py-2"><p class="text-[11px] text-muted-foreground">' +
            escHtml(c.author) +
            '</p><p class="mt-1 whitespace-pre-wrap">' +
            escHtml(c.body) +
            "</p></div>"
        );
      });
    } else {
      lines.push('<p class="mt-1 text-muted-foreground">No comments.</p>');
    }
    lines.push("</div>");

    lines.push('<div class="pt-2"><label class="text-xs font-medium text-muted-foreground">Comment</label>');
    lines.push(
      '<textarea id="jira-comment-body" class="inv-list-control mt-1 min-h-[72px] w-full text-sm" rows="2"></textarea>'
    );
    lines.push(
      '<button type="button" id="jira-comment-btn" class="mt-2 rounded-lg bg-primary px-3 py-2 text-sm font-medium text-primary-foreground" data-issue="' +
        issue.id +
        '">Comment</button></div>'
    );

    var detailUrl =
      "/dashboard/jiraclone/issue/" + encodeURIComponent(projectKey) + "/" + issue.id + "/";
    lines.push(
      '<p class="pt-2"><a href="' +
        detailUrl +
        '" class="text-xs text-primary hover:underline">Open full page</a></p>'
    );

    lines.push("</div>");
    drawerBody.innerHTML = lines.join("");

    var fieldsSave = qs("#jira-fields-save", drawerBody);
    if (fieldsSave) {
      fieldsSave.addEventListener("click", function () {
        var dueEl = qs("#jira-due-date", drawerBody);
        var sel = qs("#jira-assignees", drawerBody);
        var ids = [];
        if (sel) {
          for (var i = 0; i < sel.options.length; i++) {
            if (sel.options[i].selected) ids.push(parseInt(sel.options[i].value, 10));
          }
        }
        var payload = {
          assignee_ids: ids,
          due_date: dueEl && dueEl.value ? dueEl.value : null,
        };
        postJson(
          apiUrl("/project/" + encodeURIComponent(projectKey) + "/issue/" + issue.id + "/fields/"),
          payload
        ).then(function (res) {
          if (res.ok && res.data.ok) window.location.reload();
          else alert((res.data && res.data.error) || "Save failed");
        });
      });
    }

    var stSel = qs("#jira-drawer-status", drawerBody);
    if (stSel && issue.can_manage) {
      stSel.addEventListener("change", function () {
        var sid = parseInt(stSel.value, 10);
        postJson(apiUrl("/project/" + encodeURIComponent(projectKey) + "/issue/" + issue.id + "/status/"), {
          status_id: sid,
        }).then(function (res) {
          if (res.ok && res.data.ok) {
            window.location.reload();
          } else {
            alert((res.data && res.data.error) || "Could not update status");
          }
        });
      });
    }

    qsa(".jira-open-sub", drawerBody).forEach(function (btn) {
      btn.addEventListener("click", function () {
        var id = btn.getAttribute("data-id");
        if (id) loadIssueIntoDrawer(id);
      });
    });

    var subBtn = qs("#jira-subtask-btn", drawerBody);
    if (subBtn) {
      subBtn.addEventListener("click", function () {
        var summary = (qs("#jira-subtask-summary", drawerBody) || {}).value || "";
        if (!summary.trim()) return;
        postJson(apiUrl("/project/" + encodeURIComponent(projectKey) + "/subtask/"), {
          parent_id: parseInt(subBtn.getAttribute("data-parent"), 10),
          summary: summary.trim(),
        }).then(function (res) {
          if (res.ok && res.data.ok) {
            loadIssueIntoDrawer(issue.id);
          } else {
            alert((res.data && res.data.error) || "Failed");
          }
        });
      });
    }

    var cbtn = qs("#jira-comment-btn", drawerBody);
    if (cbtn) {
      cbtn.addEventListener("click", function () {
        var body = (qs("#jira-comment-body", drawerBody) || {}).value || "";
        if (!body.trim()) return;
        postJson(apiUrl("/project/" + encodeURIComponent(projectKey) + "/issue/" + issue.id + "/comment/"), {
          body: body.trim(),
        }).then(function (res) {
          if (res.ok && res.data.ok) {
            loadIssueIntoDrawer(issue.id);
          } else {
            alert((res.data && res.data.error) || "Failed");
          }
        });
      });
    }
  }

  function loadIssueIntoDrawer(issueId) {
    if (drawerTitle) drawerTitle.textContent = "Loading…";
    openDrawer();
    getJson(apiUrl("/project/" + encodeURIComponent(projectKey) + "/issue/" + issueId + "/")).then(function (res) {
      if (!res.ok || !res.data.ok || !res.data.issue) {
        if (drawerBody) drawerBody.innerHTML = '<p class="text-sm text-destructive">Could not load issue.</p>';
        return;
      }
      var iss = res.data.issue;
      if (drawerTitle) drawerTitle.textContent = iss.issue_key + " — " + iss.summary;
      renderIssue(iss);
    });
  }

  if (canManage && typeof Sortable !== "undefined") {
    qsa(".jira-column-body").forEach(function (el) {
      Sortable.create(el, {
        group: "jira-board",
        animation: 150,
        handle: ".jira-drag-handle",
        draggable: ".jira-card",
        onEnd: function (evt) {
          var issueId = parseInt(evt.item.getAttribute("data-issue-id") || "0", 10);
          var toStatus = parseInt(evt.to.getAttribute("data-status-id") || "0", 10);
          var newIndex = evt.newIndex;
          if (!issueId || !toStatus) return;
          postJson(apiUrl("/project/" + encodeURIComponent(projectKey) + "/board/move/"), {
            issue_id: issueId,
            status_id: toStatus,
            position: newIndex,
          }).then(function (res) {
            if (!res.ok || !res.data.ok) {
              alert((res.data && res.data.error) || "Move failed");
              window.location.reload();
            }
          });
        },
      });
    });
  }

  root.addEventListener(
    "click",
    function (e) {
      var card = e.target.closest(".jira-card");
      if (!card || !root.contains(card)) return;
      if (e.target.closest(".jira-drag-handle, a, button, select, input, textarea")) return;
      var id = card.getAttribute("data-issue-id");
      if (id) loadIssueIntoDrawer(id);
    },
    true
  );

  qsa(".jira-quick-create-btn").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var col = btn.closest(".jira-column");
      var statusId = col ? col.getAttribute("data-status-id") : null;
      var inp = col ? qs(".jira-quick-input", col) : null;
      var summary = inp ? inp.value.trim() : "";
      if (!summary || !statusId) return;
      postJson(apiUrl("/project/" + encodeURIComponent(projectKey) + "/issues/quick-create/"), {
        summary: summary,
        status_id: parseInt(statusId, 10),
      }).then(function (res) {
        if (res.ok && res.data.ok) {
          window.location.reload();
        } else {
          alert((res.data && res.data.error) || "Could not create");
        }
      });
    });
  });
})();
