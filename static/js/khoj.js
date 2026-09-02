/* Khoj — landing page behaviour.
   Vanilla ES6, no dependencies. Every component here is an enhancement:
   the page is complete and readable before any of it runs. */

(function () {
  "use strict";

  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------------------------------------------------- theme toggle */

  var root = document.documentElement;
  var themeBtn = document.querySelector("[data-theme-toggle]");
  if (themeBtn) {
    themeBtn.addEventListener("click", function () {
      // No stored value means "follow the OS", so the first click has to
      // resolve what the OS is currently saying before flipping it.
      var current = root.getAttribute("data-theme");
      if (!current) {
        current = window.matchMedia("(prefers-color-scheme: dark)").matches
          ? "dark"
          : "light";
      }
      var next = current === "dark" ? "light" : "dark";
      root.setAttribute("data-theme", next);
      try {
        localStorage.setItem("khoj-theme", next);
      } catch (e) {
        /* private mode; the toggle still works for this page view */
      }
    });
  }

  /* ------------------------------------------- sticky header compaction */

  var header = document.querySelector(".site-header");
  var hero = document.querySelector(".hero");
  if (header && hero && "IntersectionObserver" in window) {
    new IntersectionObserver(
      function (entries) {
        header.classList.toggle("is-compact", !entries[0].isIntersecting);
      },
      { rootMargin: "-80px 0px 0px 0px" }
    ).observe(hero);
  }

  /* -------------------------------------------------- scroll rail + draw */

  var bands = Array.prototype.slice.call(document.querySelectorAll("[data-band]"));
  var railBtns = Array.prototype.slice.call(document.querySelectorAll(".rail button"));

  railBtns.forEach(function (btn) {
    btn.addEventListener("click", function () {
      var target = document.getElementById(btn.dataset.target);
      if (target) target.scrollIntoView({ behavior: reduced ? "auto" : "smooth" });
    });
  });

  if (bands.length && "IntersectionObserver" in window) {
    var railObserver = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          railBtns.forEach(function (b) {
            b.setAttribute("aria-current", String(b.dataset.target === entry.target.id));
          });
        });
      },
      { threshold: 0.35 }
    );
    bands.forEach(function (b) { railObserver.observe(b); });
  }

  /* ------------------------------------------------------- path drawing */

  // Each path is told its own length so the dash animation is exact
  // regardless of how the SVG was drawn.
  document.querySelectorAll(".draw").forEach(function (path) {
    if (typeof path.getTotalLength === "function") {
      path.style.setProperty("--len", path.getTotalLength());
    }
  });

  if ("IntersectionObserver" in window) {
    var drawObserver = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-drawn");
            drawObserver.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.3 }
    );
    document.querySelectorAll("[data-draw]").forEach(function (el) {
      drawObserver.observe(el);
    });
  }

  /* ----------------------------------------------------------- counters */

  function countUp(el) {
    var target = parseInt(el.dataset.count, 10);
    if (isNaN(target) || reduced || target === 0) return;
    var start = performance.now();
    var dur = 700;
    function frame(now) {
      var t = Math.min((now - start) / dur, 1);
      var eased = 1 - Math.pow(1 - t, 3);
      el.textContent = Math.round(target * eased).toLocaleString();
      if (t < 1) requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
  }

  if ("IntersectionObserver" in window) {
    var countObserver = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            countUp(entry.target);
            countObserver.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.6 }
    );
    document.querySelectorAll("[data-count]").forEach(function (el) {
      countObserver.observe(el);
    });
  }

  /* ------------------------------------------------------------ stepper */

  var steps = Array.prototype.slice.call(document.querySelectorAll(".step"));
  if (steps.length) {
    var current = 0;
    var timer = null;

    function show(i) {
      current = (i + steps.length) % steps.length;
      steps.forEach(function (s, n) {
        s.setAttribute("aria-current", String(n === current));
      });
      document.querySelectorAll("[data-step-state]").forEach(function (g) {
        var on = parseInt(g.dataset.stepState, 10) <= current;
        g.classList.toggle("on", on);
      });
    }

    function play() {
      if (reduced) return;
      stop();
      timer = setInterval(function () { show(current + 1); }, 6000);
    }
    function stop() { if (timer) clearInterval(timer); timer = null; }

    steps.forEach(function (s, n) {
      s.addEventListener("click", function () { show(n); play(); });
      s.addEventListener("keydown", function (e) {
        if (e.key === "ArrowDown" || e.key === "ArrowRight") {
          e.preventDefault(); show(current + 1); steps[current].focus(); play();
        } else if (e.key === "ArrowUp" || e.key === "ArrowLeft") {
          e.preventDefault(); show(current - 1); steps[current].focus(); play();
        }
      });
    });

    var stepper = document.querySelector(".stepper");
    if (stepper) {
      stepper.addEventListener("mouseenter", stop);
      stepper.addEventListener("mouseleave", play);
      stepper.addEventListener("focusin", stop);
      stepper.addEventListener("focusout", play);
    }

    show(0);
    play();
  }

  /* --------------------------------------------------------- match demo
     Weights are hard-coded from CLAUDE.md §Matching engine. This is a
     teaching toy, deliberately not a call to the real engine. */

  var demo = document.querySelector("[data-demo]");
  if (demo) {
    var CIRCUMFERENCE = 2 * Math.PI * 54;
    var dial = demo.querySelector(".value");
    var out = demo.querySelector("[data-score]");
    var verdict = demo.querySelector(".verdict");
    var attrs = Array.prototype.slice.call(demo.querySelectorAll(".demo-toggle"));

    function render() {
      var total = 0;
      var marks = 0;

      attrs.forEach(function (btn) {
        var on = btn.getAttribute("aria-pressed") === "true";
        var pts = on ? parseInt(btn.dataset.points, 10) : 0;
        total += pts;
        if (btn.dataset.signal === "marks") marks = pts;

        var bar = demo.querySelector('[data-bar="' + btn.dataset.signal + '"]');
        if (bar) {
          bar.style.width = (pts / parseInt(btn.dataset.max, 10)) * 100 + "%";
        }
        var pts_el = demo.querySelector('[data-pts="' + btn.dataset.signal + '"]');
        if (pts_el) pts_el.textContent = pts + "/" + btn.dataset.max;
      });

      if (out) out.textContent = total;
      if (dial) {
        dial.style.strokeDasharray = CIRCUMFERENCE;
        dial.style.strokeDashoffset = CIRCUMFERENCE * (1 - total / 100);
      }

      if (verdict) {
        // A strong marks hit is always surfaced, whatever the total says.
        var band, text;
        if (marks > 15) {
          band = "surface";
          text = verdict.dataset.textMarks;
        } else if (total > 55) {
          band = "surface"; text = verdict.dataset.textSurface;
        } else if (total >= 30) {
          band = "weak"; text = verdict.dataset.textWeak;
        } else {
          band = "discard"; text = verdict.dataset.textDiscard;
        }
        verdict.dataset.band = band;
        verdict.textContent = text;
      }
    }

    attrs.forEach(function (btn) {
      btn.addEventListener("click", function () {
        btn.setAttribute(
          "aria-pressed",
          btn.getAttribute("aria-pressed") === "true" ? "false" : "true"
        );
        render();
      });
    });

    render();
  }

  /* ------------------------------------------------------- district map */

  var districtBtns = Array.prototype.slice.call(document.querySelectorAll(".district-btn"));
  if (districtBtns.length) {
    districtBtns.forEach(function (btn) {
      btn.addEventListener("click", function () {
        var key = btn.dataset.district;
        districtBtns.forEach(function (b) {
          b.setAttribute("aria-pressed", String(b === btn));
        });
        document.querySelectorAll("[data-district-panel]").forEach(function (p) {
          p.hidden = p.dataset.districtPanel !== key;
        });
      });
    });
  }
})();
