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
  var auj = document.getElementById("jira-assignable-users-json");
  if (auj) {
    try {
      window.__jiraAssignableUsers = JSON.parse(auj.textContent);
    } catch (e) {
      window.__jiraAssignableUsers = [];
    }
  } else {
    window.__jiraAssignableUsers = [];
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
  var deptPanel = qs("#jira-dept-panel");
  var btnOpenDeptPanel = qs("#jira-open-dept-panel");
  var btnCloseDeptPanel = qs("#jira-dept-panel-close");
  var allDepartmentEmployees = [];
  var selectedEmployeeIdSet = {};
  var assignmentByDeptId = {};

  function closeDrawer() {
    if (!drawer) return;
    drawer.classList.add("hidden");
    drawer.classList.remove("flex");
    drawer.setAttribute("aria-hidden", "true");
    if (drawerBackdrop) drawerBackdrop.classList.add("hidden");
    document.body.classList.remove("overflow-hidden");
  }

  function openDrawer() {
    if (!drawer) return;
    drawer.classList.remove("hidden");
    drawer.classList.add("flex");
    drawer.setAttribute("aria-hidden", "false");
    if (drawerBackdrop) drawerBackdrop.classList.remove("hidden");
    document.body.classList.add("overflow-hidden");
  }

  if (btnCloseDrawer) btnCloseDrawer.addEventListener("click", closeDrawer);
  if (drawerBackdrop) drawerBackdrop.addEventListener("click", closeDrawer);

  function openDeptPanel() {
    if (!deptPanel) return;
    deptPanel.classList.remove("hidden");
    deptPanel.classList.add("flex");
    if (drawerBackdrop) drawerBackdrop.classList.remove("hidden");
    document.body.classList.add("overflow-hidden");
    loadDepartmentOptions();
    loadDepartmentAssignments();
  }
  function closeDeptPanel() {
    if (!deptPanel) return;
    deptPanel.classList.add("hidden");
    deptPanel.classList.remove("flex");
    if (drawerBackdrop) drawerBackdrop.classList.add("hidden");
    document.body.classList.remove("overflow-hidden");
  }
  if (btnOpenDeptPanel) btnOpenDeptPanel.addEventListener("click", openDeptPanel);
  if (btnCloseDeptPanel) btnCloseDeptPanel.addEventListener("click", closeDeptPanel);

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
      lines.push('<div class="rounded-lg border border-border p-3 space-y-2">');
      lines.push('<p class="text-xs font-semibold uppercase text-muted-foreground">Quick edit</p>');
      lines.push('<label class="text-xs text-muted-foreground">Summary</label>');
      lines.push('<input id="jira-inline-summary" class="inv-list-control w-full text-sm" value="' + escHtml(issue.summary || "") + '" />');
      lines.push('<label class="text-xs text-muted-foreground">Description</label>');
      lines.push('<textarea id="jira-inline-description" class="inv-list-control w-full min-h-[90px] text-sm">' + escHtml(issue.description || "") + "</textarea>");
      lines.push(
        '<button type="button" id="jira-inline-save" class="rounded-lg bg-primary px-3 py-2 text-xs font-medium text-primary-foreground">Save issue</button>'
      );
      lines.push("</div>");
    }

    if (issue.can_manage) {
      var dueVal = issue.due_date ? String(issue.due_date).slice(0, 10) : "";
      lines.push('<div class="rounded-lg border border-border p-3 space-y-2">');
      lines.push('<p class="text-xs font-semibold uppercase text-muted-foreground">Due date &amp; assignees</p>');
      if (issue.departments_configured === false) {
        lines.push(
          '<p class="text-[11px] text-muted-foreground">No department mapping yet — map departments/employees to enable assignee control.</p>'
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

    lines.push("</div>");
    drawerBody.innerHTML = lines.join("");

    var inlineSave = qs("#jira-inline-save", drawerBody);
    if (inlineSave) {
      inlineSave.addEventListener("click", function () {
        var payload = {
          summary: (qs("#jira-inline-summary", drawerBody) || {}).value || "",
          description: (qs("#jira-inline-description", drawerBody) || {}).value || "",
        };
        postJson(
          apiUrl("/project/" + encodeURIComponent(projectKey) + "/issue/" + issue.id + "/inline-update/"),
          payload
        ).then(function (res) {
          if (res.ok && res.data.ok) {
            loadIssueIntoDrawer(issue.id);
            window.location.reload();
          } else {
            alert((res.data && res.data.error) || "Save failed");
          }
        });
      });
    }

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

  root.addEventListener("click", function (e) {
    var openBtn = e.target.closest(".jira-open-issue");
    if (openBtn && root.contains(openBtn)) {
      var openId = openBtn.getAttribute("data-issue-id");
      if (openId) loadIssueIntoDrawer(openId);
      return;
    }
    var card = e.target.closest(".jira-card");
    if (!card || !root.contains(card)) return;
    if (e.target.closest(".jira-drag-handle, a, button, select, input, textarea, summary, details")) return;
    var id = card.getAttribute("data-issue-id");
    if (id) loadIssueIntoDrawer(id);
  });

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

  qsa(".jira-open-issue").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var id = btn.getAttribute("data-issue-id");
      if (id) loadIssueIntoDrawer(id);
    });
  });

  function loadDepartmentOptions(preferredDepartmentId) {
    var deptSelect = qs("#jira-dept-id");
    var empSelect = qs("#jira-dept-employees");
    if (!deptSelect || !empSelect) return;
    getJson(apiUrl("/project/" + encodeURIComponent(projectKey) + "/department-employees/")).then(function (res) {
      if (!res.ok || !res.data.ok) return;
      var mapped = res.data.departments || [];
      var available = res.data.available_departments || [];
      var optionChunks = [];
      if (mapped.length) {
        optionChunks.push(
          '<optgroup label="Project linked departments">' +
            mapped
              .map(function (d) {
                return '<option value="' + d.id + '">' + escHtml((d.code ? d.code + " - " : "") + d.name) + "</option>";
              })
              .join("") +
            "</optgroup>"
        );
      }
      if (available.length) {
        optionChunks.push(
          '<optgroup label="Add new department link">' +
            available
              .map(function (d) {
                return '<option value="' + d.id + '">' + escHtml((d.code ? d.code + " - " : "") + d.name) + "</option>";
              })
              .join("") +
            "</optgroup>"
        );
      }
      deptSelect.innerHTML = optionChunks.join("");
      allDepartmentEmployees = res.data.employees || [];
      if (!deptSelect.options.length) {
        deptSelect.value = "";
      } else {
        deptSelect.value = preferredDepartmentId ? String(preferredDepartmentId) : (deptSelect.value || deptSelect.options[0].value);
      }
      renderDepartmentChips();
      renderDepartmentEmployees();
    });
  }

  function renderDepartmentChips() {
    var wrap = qs("#jira-dept-chip-list");
    var deptSelect = qs("#jira-dept-id");
    var totalChip = qs("#jira-dept-total");
    if (!wrap || !deptSelect) return;
    var current = String(deptSelect.value || "");
    var options = qsa("#jira-dept-id option");
    if (totalChip) totalChip.textContent = options.length + " total";
    wrap.innerHTML = options
      .map(function (o) {
        var did = String(o.value || "");
        if (!did) return "";
        var active = current && current === did;
        var linked = !!assignmentByDeptId[did];
        var memberCount = linked ? ((assignmentByDeptId[did].employees || []).length || 0) : 0;
        return (
          '<button type="button" class="jira-dept-chip rounded-xl border p-3 text-left transition-colors ' +
          (active ? "border-primary bg-primary/10 shadow-sm" : "border-border bg-background hover:bg-accent") +
          '" data-id="' + did + '">' +
          '<div class="flex items-start justify-between gap-2">' +
          '<div class="min-w-0">' +
          '<p class="truncate text-sm font-semibold ' + (active ? "text-primary" : "text-foreground") + '">' + escHtml(o.textContent || "Department") + "</p>" +
          '<p class="mt-0.5 text-[10px] uppercase tracking-wide ' + (active ? "text-primary/80" : "text-muted-foreground") + '">' + memberCount + " assigned</p>" +
          "</div>" +
          '<span class="mt-0.5 inline-flex h-5 w-5 items-center justify-center rounded-full ' + (active ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground") + '">' +
          '<i data-lucide="' + (linked ? "check" : "plus") + '" class="h-3 w-3"></i>' +
          "</span></div>" +
          "</button>"
        );
      })
      .join("");
    if (!wrap.innerHTML.trim()) {
      wrap.innerHTML = '<p class="rounded-lg border border-dashed border-border px-3 py-2 text-xs text-muted-foreground">No department yet.</p>';
      return;
    }
    qsa(".jira-dept-chip", wrap).forEach(function (btn) {
      btn.addEventListener("click", function () {
        var did = btn.getAttribute("data-id");
        if (!did) return;
        applyDepartmentSelection(did);
      });
    });
    if (window.lucide && typeof window.lucide.createIcons === "function") window.lucide.createIcons();
  }

  function applyDepartmentSelection(departmentId) {
    var deptSelect = qs("#jira-dept-id");
    var orderEl = qs("#jira-dept-order");
    var editIdEl = qs("#jira-edit-dept-assignment-id");
    if (!deptSelect) return;
    deptSelect.value = String(departmentId || "");
    var row = assignmentByDeptId[String(departmentId || "")];
    if (row) {
      var empSet = {};
      (row.employees || []).forEach(function (e) { empSet[String(e.id)] = true; });
      selectedEmployeeIdSet = empSet;
      if (editIdEl) editIdEl.value = row.id || "";
      if (orderEl) orderEl.value = row.order || 0;
    } else {
      selectedEmployeeIdSet = {};
      if (editIdEl) editIdEl.value = "";
      if (orderEl) orderEl.value = "0";
    }
    renderDepartmentChips();
    renderDepartmentEmployees();
  }

  function renderDepartmentEmployees() {
    var deptSelect = qs("#jira-dept-id");
    var empSelect = qs("#jira-dept-employees");
    var chipWrap = qs("#jira-employee-chip-list");
    var searchEl = qs("#jira-employee-search");
    if (!empSelect || !chipWrap) return;
    var selectedDept = deptSelect && deptSelect.value ? String(deptSelect.value) : "";
    var q = searchEl && searchEl.value ? searchEl.value.trim().toLowerCase() : "";
    var rows = (allDepartmentEmployees || []).slice();
    rows.sort(function (a, b) {
      var aMatch = selectedDept && String(a.department_id || "") === selectedDept ? 1 : 0;
      var bMatch = selectedDept && String(b.department_id || "") === selectedDept ? 1 : 0;
      if (aMatch !== bMatch) return bMatch - aMatch;
      return String(a.full_name || "").localeCompare(String(b.full_name || ""));
    });
    if (q) {
      rows = rows.filter(function (e) {
        return (
          String(e.full_name || "").toLowerCase().indexOf(q) >= 0 ||
          String(e.employee_code || "").toLowerCase().indexOf(q) >= 0
        );
      });
    }
    empSelect.innerHTML = rows
      .map(function (e) {
        var inDept = selectedDept && String(e.department_id || "") === selectedDept;
        var badge = inDept ? " [Dept]" : "";
        return (
          '<option value="' +
          e.id +
          '" data-department-id="' +
          (e.department_id || "") +
          '">' +
          escHtml((e.full_name || "Employee") + " (" + (e.employee_code || "-") + ")" + badge) +
          "</option>"
        );
      })
      .join("");
    chipWrap.innerHTML = rows
      .map(function (e) {
        var eid = String(e.id);
        var selected = !!selectedEmployeeIdSet[eid];
        var inDept = selectedDept && String(e.department_id || "") === selectedDept;
        return (
          '<button type="button" class="jira-emp-chip flex items-center justify-between gap-3 rounded-xl border px-3 py-2 text-left transition-colors ' +
          (selected ? "border-primary bg-primary/10 text-primary" : "border-border bg-background text-foreground hover:bg-accent") +
          '" data-id="' + eid + '">' +
          '<span class="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-muted text-xs font-semibold ' + (selected ? "text-primary" : "text-muted-foreground") + '">' +
          escHtml((e.full_name || "E").charAt(0).toUpperCase()) +
          "</span>" +
          '<span class="min-w-0 flex-1">' +
          '<span class="block truncate text-sm font-medium ' + (selected ? "text-primary" : "text-foreground") + '">' + escHtml(e.full_name || "Employee") + "</span>" +
          '<span class="mt-0.5 block text-[11px] ' + (selected ? "text-primary/80" : "text-muted-foreground") + '">' + escHtml(e.employee_code || "-") + "</span>" +
          "</span>" +
          '<span class="inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full border ' + (selected ? "border-primary bg-primary text-primary-foreground" : "border-border bg-background text-muted-foreground") + '">' +
          '<i data-lucide="' + (selected ? "check" : "circle") + '" class="h-3.5 w-3.5"></i>' +
          "</span>" +
          "</button>"
        );
      })
      .join("");
    if (!rows.length) {
      empSelect.innerHTML = '<option value="">No employees found</option>';
      chipWrap.innerHTML = '<p class="rounded-lg border border-dashed border-border px-3 py-3 text-xs text-muted-foreground">No employees found.</p>';
    }
    qsa(".jira-emp-chip", chipWrap).forEach(function (btn) {
      btn.addEventListener("click", function () {
        var eid = btn.getAttribute("data-id");
        if (!eid) return;
        if (selectedEmployeeIdSet[eid]) delete selectedEmployeeIdSet[eid];
        else selectedEmployeeIdSet[eid] = true;
        renderDepartmentEmployees();
        persistCurrentDepartmentAssignment();
      });
    });
    if (window.lucide && typeof window.lucide.createIcons === "function") window.lucide.createIcons();
  }

  var createDeptBtn = qs("#jira-create-dept-btn");
  if (createDeptBtn) {
    createDeptBtn.addEventListener("click", function () {
      var nameEl = qs("#jira-new-dept-name");
      var name = (nameEl && nameEl.value ? nameEl.value : "").trim();
      if (!name) {
        alert("Department name required");
        return;
      }
      postJson(apiUrl("/project/" + encodeURIComponent(projectKey) + "/departments/create/"), {
        name: name,
      }).then(function (res) {
        if (!res.ok || !res.data.ok || !res.data.department) {
          alert((res.data && res.data.error) || "Could not create department");
          return;
        }
        var dep = res.data.department;
        var deptSelect = qs("#jira-dept-id");
        if (deptSelect) {
          var exists = qsa("#jira-dept-id option").some(function (o) { return String(o.value) === String(dep.id); });
          if (!exists) {
            var opt = document.createElement("option");
            opt.value = String(dep.id);
            opt.textContent = (dep.code ? dep.code + " - " : "") + dep.name;
            deptSelect.appendChild(opt);
          }
          applyDepartmentSelection(dep.id);
        }
        // Keep source-of-truth synced from API after instant UI update
        loadDepartmentOptions(dep.id);
        if (nameEl) nameEl.value = "";
      });
    });
  }

  function selectedEmployeeIds() {
    return Object.keys(selectedEmployeeIdSet)
      .map(function (id) { return parseInt(id, 10); })
      .filter(function (n) { return !isNaN(n); });
  }

  function persistCurrentDepartmentAssignment() {
    var deptId = parseInt((qs("#jira-dept-id") || {}).value || "0", 10);
    if (!deptId) return;
    var rowId = (qs("#jira-edit-dept-assignment-id") || {}).value || "";
    var payload = {
      department_id: deptId,
      order: parseInt((qs("#jira-dept-order") || {}).value || "0", 10),
      employee_ids: selectedEmployeeIds(),
    };
    var endpoint = rowId
      ? apiUrl("/project/" + encodeURIComponent(projectKey) + "/department-assignments/" + rowId + "/")
      : apiUrl("/project/" + encodeURIComponent(projectKey) + "/department-assignments/");
    postJson(endpoint, payload).then(function (res) {
      if (!res.ok || !res.data.ok) return;
      if (res.data.assignment && res.data.assignment.id) {
        var editIdEl = qs("#jira-edit-dept-assignment-id");
        if (editIdEl) editIdEl.value = String(res.data.assignment.id);
      }
      loadDepartmentAssignments();
    });
  }

  function loadDepartmentAssignments() {
    var list = qs("#jira-dept-list");
    if (!list) return;
    getJson(apiUrl("/project/" + encodeURIComponent(projectKey) + "/department-assignments/")).then(function (res) {
      if (!res.ok || !res.data.ok) {
        list.innerHTML = '<p class="text-sm text-destructive">Could not load department assignments.</p>';
        return;
      }
      var rows = res.data.results || [];
      assignmentByDeptId = {};
      rows.forEach(function (r) {
        var did = r && r.department && r.department.id ? String(r.department.id) : "";
        if (did) assignmentByDeptId[did] = r;
      });
      renderDepartmentChips();
      if (!rows.length) {
        list.innerHTML = '<p class="text-sm text-muted-foreground">No department mapping yet.</p>';
        return;
      }
      list.innerHTML = rows
        .map(function (r) {
          var deptId = (r.department && r.department.id) || "";
          return (
            '<div class="rounded-lg border border-border bg-muted/10 p-3">' +
            '<div class="flex items-center justify-between gap-2"><p class="font-medium text-foreground">' + escHtml((r.department && r.department.name) || "Department") + '</p>' +
            '<div class="flex gap-2">' +
            '<button type="button" class="jira-dept-assign rounded-md border border-primary/30 bg-primary/10 px-2 py-1 text-xs text-primary" data-dept-id="' + deptId + '">Assign people</button>' +
            '<button type="button" class="jira-dept-edit rounded-md border border-border px-2 py-1 text-xs" data-assignment="' + encodeURIComponent(JSON.stringify(r)) + '">Edit</button>' +
            '<button type="button" class="jira-dept-delete rounded-md border border-destructive/30 px-2 py-1 text-xs text-destructive" data-id="' + r.id + '">Delete</button>' +
            "</div></div>" +
            '<p class="mt-1 text-xs text-muted-foreground">' + (r.employees || []).map(function (e) { return escHtml(e.name); }).join(", ") + "</p>" +
            "</div>"
          );
        })
        .join("");
      qsa(".jira-dept-edit", list).forEach(function (btn) {
        btn.addEventListener("click", function () {
          var row = JSON.parse(decodeURIComponent(btn.getAttribute("data-assignment") || "%7B%7D"));
          applyDepartmentSelection((row.department && row.department.id) || "");
        });
      });
      qsa(".jira-dept-assign", list).forEach(function (btn) {
        btn.addEventListener("click", function () {
          var deptId = btn.getAttribute("data-dept-id");
          if (!deptId) return;
          applyDepartmentSelection(deptId);
          var employeeSection = qs("#jira-employee-chip-list");
          if (employeeSection && typeof employeeSection.scrollIntoView === "function") {
            employeeSection.scrollIntoView({ behavior: "smooth", block: "start" });
          }
        });
      });
      qsa(".jira-dept-delete", list).forEach(function (btn) {
        btn.addEventListener("click", function () {
          var id = btn.getAttribute("data-id");
          if (!id) return;
          fetch(apiUrl("/project/" + encodeURIComponent(projectKey) + "/department-assignments/" + id + "/"), {
            method: "DELETE",
            credentials: "same-origin",
            headers: { "X-CSRFToken": csrf },
          }).then(function () {
            loadDepartmentOptions();
            loadDepartmentAssignments();
          });
        });
      });
    });
  }

  var deptSelectEl = qs("#jira-dept-id");
  if (deptSelectEl) {
    deptSelectEl.addEventListener("change", function () {
      renderDepartmentChips();
      renderDepartmentEmployees();
    });
  }
  var employeeSearchEl = qs("#jira-employee-search");
  if (employeeSearchEl) {
    employeeSearchEl.addEventListener("input", renderDepartmentEmployees);
  }

  var deptSaveBtn = qs("#jira-dept-save-btn");
  if (deptSaveBtn) {
    deptSaveBtn.addEventListener("click", function () {
      persistCurrentDepartmentAssignment();
    });
  }

  function updateCardAvatars(issueId, assigneeSelect) {
    var wrap = qs('.jira-card-assignee-avatars[data-issue-id="' + issueId + '"]');
    if (!wrap || !assigneeSelect) return;
    var chosen = [];
    for (var i = 0; i < assigneeSelect.options.length; i++) {
      if (assigneeSelect.options[i].selected) chosen.push(assigneeSelect.options[i].text || "");
    }
    if (!chosen.length) {
      wrap.innerHTML = '<span class="inline-flex h-6 w-6 items-center justify-center rounded-full border border-card bg-muted text-[10px] font-semibold text-muted-foreground" title="Unassigned">?</span>';
      return;
    }
    wrap.innerHTML = chosen.slice(0, 4).map(function (name) {
      var initial = (String(name).trim().charAt(0) || "?").toUpperCase();
      return '<span class="inline-flex h-6 w-6 items-center justify-center rounded-full border border-card bg-primary/10 text-[10px] font-semibold text-primary" title="' + escHtml(name) + '">' + escHtml(initial) + "</span>";
    }).join("");
  }

  function saveCardFields(issueId) {
    if (!issueId) return;
    var dueInput = qs('.jira-card-due[data-issue-id="' + issueId + '"]');
    var assigneeSelect = qs('.jira-card-assignees[data-issue-id="' + issueId + '"]');
    var assigneeIds = [];
    if (assigneeSelect) {
      for (var i = 0; i < assigneeSelect.options.length; i++) {
        if (assigneeSelect.options[i].selected) assigneeIds.push(parseInt(assigneeSelect.options[i].value, 10));
      }
    }
    postJson(apiUrl("/project/" + encodeURIComponent(projectKey) + "/issue/" + issueId + "/fields/"), {
      assignee_ids: assigneeIds,
      due_date: dueInput && dueInput.value ? dueInput.value : null,
    }).then(function (res) {
      if (!res.ok || !res.data.ok) {
        alert((res.data && res.data.error) || "Could not save issue fields");
        return;
      }
      updateCardAvatars(issueId, assigneeSelect);
    });
  }

  function refreshPeoplePickerChecks(issueId) {
    var assigneeSelect = qs('.jira-card-assignees[data-issue-id="' + issueId + '"]');
    if (!assigneeSelect) return;
    var selected = {};
    for (var i = 0; i < assigneeSelect.options.length; i++) {
      if (assigneeSelect.options[i].selected) selected[String(assigneeSelect.options[i].value)] = true;
    }
    qsa('.jira-people-option[data-issue-id="' + issueId + '"]').forEach(function (btn) {
      var uid = String(btn.getAttribute("data-user-id") || "");
      var tick = qs(".jira-people-check", btn);
      var isSelected = !!selected[uid];
      btn.classList.toggle("bg-accent", isSelected);
      if (tick) tick.classList.toggle("hidden", !isSelected);
    });
  }

  qsa(".jira-card-assignees").forEach(function (sel) {
    sel.addEventListener("change", function () {
      var issueId = sel.getAttribute("data-issue-id");
      saveCardFields(issueId);
      refreshPeoplePickerChecks(issueId);
    });
    var initIssueId = sel.getAttribute("data-issue-id");
    if (initIssueId) refreshPeoplePickerChecks(initIssueId);
  });

  qsa(".jira-people-option").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var issueId = btn.getAttribute("data-issue-id");
      var userId = btn.getAttribute("data-user-id");
      if (!issueId || !userId) return;
      var sel = qs('.jira-card-assignees[data-issue-id="' + issueId + '"]');
      if (!sel) return;
      for (var i = 0; i < sel.options.length; i++) {
        if (String(sel.options[i].value) === String(userId)) {
          sel.options[i].selected = !sel.options[i].selected;
          break;
        }
      }
      saveCardFields(issueId);
      refreshPeoplePickerChecks(issueId);
    });
  });

  qsa(".jira-card-due").forEach(function (inp) {
    inp.addEventListener("change", function () {
      var issueId = inp.getAttribute("data-issue-id");
      saveCardFields(issueId);
    });
  });
})();
