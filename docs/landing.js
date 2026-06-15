// JavaScript Controller for Image Color Check Landing Page
window.addEventListener('error', (event) => {
  const div = document.createElement('div');
  div.style.position = 'fixed';
  div.style.bottom = '10px';
  div.style.left = '10px';
  div.style.backgroundColor = 'rgba(239, 68, 68, 0.95)';
  div.style.color = 'white';
  div.style.padding = '12px 18px';
  div.style.borderRadius = '6px';
  div.style.zIndex = '999999';
  div.style.fontFamily = 'monospace';
  div.style.fontSize = '11px';
  div.style.maxWidth = '90vw';
  div.style.wordBreak = 'break-all';
  div.style.boxShadow = '0 10px 30px rgba(0,0,0,0.15)';
  div.innerHTML = `<strong>JS Error:</strong> ${event.message} <br> at ${event.filename}:${event.lineno}:${event.colno}`;
  document.body.appendChild(div);
});

// Register GSAP ScrollTrigger plugin
gsap.registerPlugin(ScrollTrigger);

document.addEventListener("DOMContentLoaded", () => {
  
  // ==========================================
  // 1. CONFIGURATIONS & RADAR CHART DATA
  // ==========================================
  const configData = {
    "cinematic_default": {
      stats: [80, 70, 75, 60, 65, 80], // Atmosphere, Saturation, Contrast, Saliency, Lightness, Diversity
      statsFormatted: ["80% (中高)", "70% (中高)", "75% (中高)", "60% (中等)", "0.65", "極佳 (均勻)"],
      color: "#0284c7", // blue
      bg: "#f8fafc"
    },
    "vibrant_accent": {
      stats: [40, 95, 85, 75, 50, 90],
      statsFormatted: ["40% (偏低)", "95% (極高)", "85% (高)", "75% (高)", "0.50", "極高 (鮮豔)"],
      color: "#7c3aed", // purple
      bg: "#ffffff"
    },
    "landscape_atmosphere": {
      stats: [95, 50, 40, 35, 80, 60],
      statsFormatted: ["95% (極高)", "50% (中等)", "40% (偏低)", "35% (低)", "0.80", "良好 (重背景)"],
      color: "#ea580c", // orange
      bg: "#fdfdfd"
    },
    "subject_focus": {
      stats: [55, 65, 80, 95, 55, 70],
      statsFormatted: ["55% (中等)", "65% (中等)", "80% (高)", "95% (極高)", "0.55", "中等 (聚焦主體)"],
      color: "#0d9488", // teal
      bg: "#fafafa"
    }
  };

  const center = 250;
  const maxVal = 100;
  const maxRadius = 180;
  // Angles for 6 dimensions: Atmosphere, Saturation, Contrast, Saliency, Lightness, Diversity
  const angles = [
    -Math.PI / 2,         // 12 o'clock (Atmosphere)
    -Math.PI / 6,         // 2 o'clock (Saturation)
    Math.PI / 6,          // 4 o'clock (Contrast)
    Math.PI / 2,          // 6 o'clock (Saliency)
    Math.PI * 5 / 6,      // 8 o'clock (Lightness)
    Math.PI * 7 / 6       // 10 o'clock (Diversity)
  ];

  // Calculate coordinates based on relative values
  function getCoordinates(statsValues) {
    return statsValues.map((val, i) => {
      const r = (val / maxVal) * maxRadius;
      const x = center + r * Math.cos(angles[i]);
      const y = center + r * Math.sin(angles[i]);
      return { x, y };
    });
  }

  // ==========================================
  // 2. LENIS SMOOTH SCROLL INITIALIZATION
  // ==========================================
  const lenis = new Lenis({
    duration: 1.2,
    easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
    direction: "vertical",
    smooth: true,
    mouseMultiplier: 1.0,
    smoothTouch: false
  });

  lenis.on("scroll", ScrollTrigger.update);

  gsap.ticker.add((time) => {
    lenis.raf(time * 1000);
  });
  
  gsap.ticker.lagSmoothing(0);

  // Smooth scroll to anchors
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener("click", function (e) {
      e.preventDefault();
      const targetId = this.getAttribute("href");
      if (targetId === "#") return;
      
      const targetElement = document.querySelector(targetId);
      if (targetElement) {
        document.querySelector(".mobile-menu").classList.remove("open");
        document.querySelector(".menu-toggle").classList.remove("open");
        
        lenis.scrollTo(targetElement, {
          offset: 0,
          duration: 1.5,
          easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t))
        });
      }
    });
  });

  // ==========================================
  // 3. CUSTOM MAGNETIC CURSOR
  // ==========================================
  const cursor = document.getElementById("custom-cursor");
  const cursorDot = document.getElementById("custom-cursor-dot");

  let mouseX = 0, mouseY = 0;
  let cursorX = 0, cursorY = 0;
  let cursorDotX = 0, cursorDotY = 0;

  window.addEventListener("mousemove", (e) => {
    mouseX = e.clientX;
    mouseY = e.clientY;
  });

  function updateCursor() {
    const ease = 0.15;
    cursorX += (mouseX - cursorX) * ease;
    cursorY += (mouseY - cursorY) * ease;
    cursor.style.transform = `translate3d(${cursorX}px, ${cursorY}px, 0)`;

    const dotEase = 0.35;
    cursorDotX += (mouseX - cursorDotX) * dotEase;
    cursorDotY += (mouseY - cursorDotY) * dotEase;
    cursorDot.style.transform = `translate3d(${cursorDotX}px, ${cursorDotY}px, 0)`;

    requestAnimationFrame(updateCursor);
  }
  updateCursor();

  // Hover states on hoverable elements
  const interactiveSelector = "a, button, .selector-btn, .pokemon-card, .menu-toggle";
  
  document.body.addEventListener("mouseenter", (e) => {
    if (e.target.matches && e.target.matches(interactiveSelector)) {
      document.body.classList.add("hover-interactive");
    }
  }, true);

  document.body.addEventListener("mouseleave", (e) => {
    if (e.target.matches && e.target.matches(interactiveSelector)) {
      document.body.classList.remove("hover-interactive");
    }
  }, true);

  // Magnetic Button Effect
  const magneticTargets = document.querySelectorAll(".magnetic-target");
  magneticTargets.forEach((target) => {
    target.addEventListener("mousemove", (e) => {
      const rect = target.getBoundingClientRect();
      const relX = e.clientX - (rect.left + rect.width / 2);
      const relY = e.clientY - (rect.top + rect.height / 2);
      
      gsap.to(target, {
        x: relX * 0.35,
        y: relY * 0.35,
        duration: 0.3,
        ease: "power2.out"
      });
    });

    target.addEventListener("mouseleave", () => {
      gsap.to(target, {
        x: 0,
        y: 0,
        duration: 0.5,
        ease: "elastic.out(1, 0.3)"
      });
    });
  });

  // ==========================================
  // 4. PRELOADER ENGINE
  // ==========================================
  const progressText = document.querySelector(".loader-progress");
  let loadProgress = 0;
  
  const progressInterval = setInterval(() => {
    loadProgress += Math.floor(Math.random() * 8) + 2;
    if (loadProgress >= 100) {
      loadProgress = 100;
      clearInterval(progressInterval);
      endLoader();
    }
    progressText.textContent = `${loadProgress}%`;
  }, 100);

  function endLoader() {
    const tl = gsap.timeline({
      onComplete: () => {
        document.body.classList.remove("loading");
        document.getElementById("loader").style.display = "none";
        
        // Setup radar matrix starting state
        updateStatsMatrix("cinematic_default", false);
        ScrollTrigger.refresh();
      }
    });

    tl.to(".loader-content", {
      opacity: 0,
      scale: 0.9,
      duration: 0.5,
      ease: "power3.in"
    });
    
    tl.to("#loader", {
      yPercent: -100,
      duration: 1.0,
      ease: "power4.inOut"
    }, "-=0.2");

    // Hero Reveal Timeline
    tl.from(".hero-title .title-outline", {
      opacity: 0,
      y: 60,
      skewY: 5,
      duration: 1.2,
      ease: "power4.out"
    }, "-=0.3");

    tl.from(".hero-title .title-solid", {
      opacity: 0,
      y: 80,
      skewY: 7,
      duration: 1.2,
      ease: "power4.out"
    }, "-=1.0");

    tl.from(".hero-chart-img", {
      opacity: 0,
      scale: 0.8,
      y: 100,
      duration: 1.5,
      ease: "power3.out"
    }, "-=1.0");

    tl.from(".hero-subtitle, .scroll-indicator, .nav-header", {
      opacity: 0,
      y: 20,
      duration: 0.8,
      stagger: 0.1,
      ease: "power2.out"
    }, "-=0.8");
  }

  // ==========================================
  // 5. RESPONSIVE MENU TOGGLE
  // ==========================================
  const menuToggle = document.querySelector(".menu-toggle");
  const mobileMenu = document.querySelector(".mobile-menu");
  
  menuToggle.addEventListener("click", () => {
    menuToggle.classList.toggle("open");
    mobileMenu.classList.toggle("open");
    
    if (mobileMenu.classList.contains("open")) {
      lenis.stop();
      gsap.fromTo(".mobile-nav-link", {
        opacity: 0,
        y: 30
      }, {
        opacity: 1,
        y: 0,
        stagger: 0.15,
        duration: 0.6,
        ease: "power3.out"
      });
    } else {
      lenis.start();
    }
  });

  document.querySelectorAll(".mobile-nav-link").forEach(link => {
    link.addEventListener("click", () => {
      lenis.start();
    });
  });

  // ==========================================
  // 6. SCROLL PROGRESS BAR
  // ==========================================
  window.addEventListener("scroll", () => {
    const totalScroll = document.documentElement.scrollHeight - window.innerHeight;
    if (totalScroll > 0) {
      const scrollPercent = (window.scrollY / totalScroll) * 100;
      document.getElementById("progress-bar").style.width = `${scrollPercent}%`;
    }
  });

  ScrollTrigger.create({
    start: "top -50px",
    onEnter: () => document.querySelector(".nav-header").classList.add("scrolled"),
    onLeaveBack: () => document.querySelector(".nav-header").classList.remove("scrolled")
  });

  // ==========================================
  // 7. PARALLAX EFFECTS (HERO & ROWS)
  // ==========================================
  document.querySelectorAll("[data-depth]").forEach((layer) => {
    const depth = parseFloat(layer.getAttribute("data-depth"));
    gsap.to(layer, {
      y: () => window.innerHeight * depth * 0.5,
      ease: "none",
      scrollTrigger: {
        trigger: "#hero",
        start: "top top",
        end: "bottom top",
        scrub: true
      }
    });
  });

  // Hero Image Card Fly-Away & Vignette Fade
  gsap.to(".hero-chart-img", {
    yPercent: -20,
    scale: 1.05,
    opacity: 0.3,
    ease: "power1.inOut",
    scrollTrigger: {
      trigger: "#hero",
      start: "top top",
      end: "bottom top",
      scrub: true
    }
  });

  // Parallax on row big numbers
  document.querySelectorAll(".bg-number").forEach((num) => {
    const speed = parseFloat(num.getAttribute("data-speed"));
    gsap.to(num, {
      yPercent: speed * 150,
      ease: "none",
      scrollTrigger: {
        trigger: num.parentElement,
        start: "top bottom",
        end: "bottom top",
        scrub: true
      }
    });
  });

  // ==========================================
  // 8. PROGRESSIVE REVEALS & THEME TRANSITIONS
  // ==========================================
  document.querySelectorAll(".showcase-row").forEach((row) => {
    const themeColor = row.getAttribute("data-theme");
    const bgColor = row.getAttribute("data-bg");
    const revealSvg = row.querySelector(".showcase-svg");
    const nameText = row.querySelector(".reveal-text");
    const fadeEls = row.querySelectorAll(".reveal-fade");

    if (revealSvg) {
      const isReverse = row.classList.contains("row-reverse");
      
      const enterX = isReverse ? 80 : -80;
      const enterY = 60;
      const enterRot = isReverse ? 15 : -15;
      
      const exitX = isReverse ? -80 : 80;
      const exitY = -60;
      const exitRot = isReverse ? -15 : 15;

      const ptl = gsap.timeline({
        scrollTrigger: {
          trigger: row,
          start: "top bottom",
          end: "bottom top",
          scrub: true
        }
      });

      ptl.fromTo(revealSvg, 
        {
          xPercent: enterX,
          yPercent: enterY,
          scale: 0.6,
          rotation: enterRot,
          opacity: 0
        },
        {
          xPercent: 0,
          yPercent: 0,
          scale: 1.0,
          rotation: 0,
          opacity: 1,
          ease: "power1.out",
          duration: 1
        }
      );

      ptl.to(revealSvg, 
        {
          xPercent: exitX,
          yPercent: exitY,
          scale: 0.8,
          rotation: exitRot,
          opacity: 0,
          ease: "power1.in",
          duration: 1
        },
        "+=0.25"
      );
    }

    if (nameText) {
      gsap.from(nameText, {
        yPercent: 100,
        opacity: 0,
        duration: 1.0,
        ease: "power3.out",
        scrollTrigger: {
          trigger: row,
          start: "top 65%",
        }
      });
    }

    if (fadeEls.length > 0) {
      gsap.to(fadeEls, {
        opacity: 1,
        y: 0,
        duration: 1.0,
        stagger: 0.15,
        ease: "power3.out",
        scrollTrigger: {
          trigger: row,
          start: "top 60%",
        }
      });
    }

    // Color morphing across panels (Vibrant Light Theme Accent switches)
    ScrollTrigger.create({
      trigger: row,
      start: "top 50%",
      end: "bottom 50%",
      onToggle: (self) => {
        if (self.isActive) {
          gsap.to(":root", {
            "--accent-color": `var(--color-${themeColor})`,
            "--bg-dark": bgColor,
            duration: 1.0,
            ease: "power2.out"
          });
        }
      }
    });
  });

  // ==========================================
  // 9. STATS MATRIX MORPHING ENGINE (Presets comparison)
  // ==========================================
  let radarInitiallyDrawn = false;
  ScrollTrigger.create({
    trigger: "#stats-matrix",
    start: "top 60%",
    onEnter: () => {
      if (!radarInitiallyDrawn) {
        updateStatsMatrix("cinematic_default", true);
        radarInitiallyDrawn = true;
      }
    }
  });

  function updateStatsMatrix(configKey, animate = true) {
    const data = configData[configKey];
    if (!data) return;

    const coords = getCoordinates(data.stats);
    const pointsString = coords.map(c => `${c.x.toFixed(1)},${c.y.toFixed(1)}`).join(" ");

    if (animate) {
      // Morph SVG radar polygon shape
      gsap.to("#radar-poly", {
        attr: { points: pointsString },
        fill: `${data.color}25`, // Hex 15% opacity
        stroke: data.color,
        duration: 0.8,
        ease: "power2.out"
      });

      // Reposition vertex points
      const idMap = ["#v-accuracy", "#v-f1", "#v-return", "#v-risk", "#v-sharpe", "#v-cost"];
      coords.forEach((coord, index) => {
        gsap.to(idMap[index], {
          attr: { cx: coord.x, cy: coord.y },
          stroke: data.color,
          duration: 0.8,
          ease: "power2.out"
        });
      });

      // Update text values and progress fill bars
      const statKeys = ["accuracy", "f1", "return", "risk", "sharpe", "cost"];
      data.stats.forEach((val, index) => {
        const key = statKeys[index];
        const barFill = document.getElementById(`fill-${key}`);
        const textVal = document.getElementById(`val-${key}`);
        
        // Progress bar width uses relative value
        gsap.to(barFill, {
          width: `${val}%`,
          backgroundColor: data.color,
          duration: 0.8,
          ease: "power2.out"
        });

        // Set text directly from formatted array
        textVal.textContent = data.statsFormatted[index];
      });

      // Dynamic Section Glow
      gsap.to(".stats-bg-glow", {
        background: `radial-gradient(circle, ${data.color}1c 0%, rgba(255, 255, 255, 0) 70%)`,
        duration: 1.0
      });
      
    } else {
      // Immediate non-animated layout setup
      document.getElementById("radar-poly").setAttribute("points", pointsString);
      document.getElementById("radar-poly").style.stroke = data.color;
      document.getElementById("radar-poly").style.fill = `${data.color}25`;
      
      const idMap = ["#v-accuracy", "#v-f1", "#v-return", "#v-risk", "#v-sharpe", "#v-cost"];
      coords.forEach((coord, i) => {
        const el = document.getElementById(idMap[i].substring(1));
        el.setAttribute("cx", coord.x);
        el.setAttribute("cy", coord.y);
        el.style.stroke = data.color;
      });
    }
  }

  // Register click events for Preset selectors
  document.querySelectorAll(".selector-btn").forEach(btn => {
    btn.addEventListener("click", function () {
      document.querySelectorAll(".selector-btn").forEach(b => b.classList.remove("active"));
      this.classList.add("active");

      const configKey = this.getAttribute("data-config");
      const data = configData[configKey];
      
      // Mutate UI theme accent colors
      gsap.to(":root", {
        "--accent-color": data.color,
        "--bg-dark": data.bg,
        duration: 0.8
      });

      updateStatsMatrix(configKey, true);
    });
  });

  // Stagger reveal text elements in stats
  gsap.from(".stats-content .reveal-text", {
    yPercent: 100,
    opacity: 0,
    duration: 1.0,
    ease: "power3.out",
    scrollTrigger: {
      trigger: "#stats-matrix",
      start: "top 65%",
    }
  });

  gsap.to(".stats-content .reveal-fade, .stats-visual", {
    opacity: 1,
    y: 0,
    duration: 1.0,
    stagger: 0.15,
    ease: "power3.out",
    scrollTrigger: {
      trigger: "#stats-matrix",
      start: "top 60%",
    }
  });

  // ==========================================
  // 10. CATALOG / DELIVERABLES CARD SPOTLIGHT
  // ==========================================
  document.querySelectorAll(".pokemon-card").forEach(card => {
    card.addEventListener("mousemove", (e) => {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      
      card.style.setProperty("--mouse-x", `${x}px`);
      card.style.setProperty("--mouse-y", `${y}px`);
    });
  });

  // Stagger reveal explorer grid
  gsap.from(".explorer-header .reveal-text", {
    yPercent: 100,
    opacity: 0,
    duration: 1.0,
    ease: "power3.out",
    scrollTrigger: {
      trigger: "#explorer",
      start: "top 70%",
    }
  });

  gsap.to(".explorer-header .reveal-fade, .explorer-grid", {
    opacity: 1,
    y: 0,
    duration: 1.0,
    stagger: 0.15,
    ease: "power3.out",
    scrollTrigger: {
      trigger: "#explorer",
      start: "top 65%",
    }
  });

});
