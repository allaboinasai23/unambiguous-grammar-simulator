/**
 * FLA Academic Project: Unambiguous Grammar Construction Simulator
 * Frontend Logic: Tree Layout Engine, SVG Renderer, Simulation Player & Comparison
 */

// Global State
const State = {
  currentGrammar: "unambiguous",
  currentExpression: "id + id * id",
  simulationData: null,
  comparisonData: null,
  activeTreeIndex: 0,
  currentStepIndex: 0,
  isPlaying: false,
  playbackTimer: null,
  playbackSpeedMs: 1000,
  zoomTransform: { x: 0, y: 0, k: 1 },
  isDragging: false,
  dragStart: { x: 0, y: 0 }
};

// ==============================================================================
// PARSE TREE HIERARCHICAL LAYOUT ALGORITHM
// ==============================================================================

class TreeLayoutEngine {
  constructor(nodeRadius = 22, levelHeight = 75, siblingGap = 35) {
    this.nodeRadius = nodeRadius;
    this.levelHeight = levelHeight;
    this.siblingGap = siblingGap;
  }

  /**
   * Computes (x, y) coordinates for all nodes in the parse tree.
   * Uses post-order traversal to determine subtree widths and center parents over children.
   */
  layout(rootNode) {
    if (!rootNode) return null;

    // Step 1: Assign depths and calculate subtree bounding widths
    const assignSubtreeWidth = (node, depth = 0) => {
      node.depth = depth;
      node.y = depth * this.levelHeight + 45;

      if (!node.children || node.children.length === 0) {
        node.subtreeWidth = this.nodeRadius * 2 + this.siblingGap;
        return;
      }

      let totalWidth = 0;
      for (const child of node.children) {
        assignSubtreeWidth(child, depth + 1);
        totalWidth += child.subtreeWidth;
      }
      node.subtreeWidth = Math.max(totalWidth, this.nodeRadius * 2 + this.siblingGap);
    };

    assignSubtreeWidth(rootNode);

    // Step 2: Assign x positions
    let currentX = 0;
    const assignPositions = (node, leftBound) => {
      if (!node.children || node.children.length === 0) {
        node.x = leftBound + node.subtreeWidth / 2;
        return;
      }

      let childLeft = leftBound;
      for (const child of node.children) {
        assignPositions(child, childLeft);
        childLeft += child.subtreeWidth;
      }

      // Center parent over first and last child
      const firstChildX = node.children[0].x;
      const lastChildX = node.children[node.children.length - 1].x;
      node.x = (firstChildX + lastChildX) / 2;
    };

    assignPositions(rootNode, 30);

    // Compute bounding box
    let minX = Infinity, maxX = -Infinity, maxY = 0;
    const computeBounds = (node) => {
      minX = Math.min(minX, node.x - this.nodeRadius);
      maxX = Math.max(maxX, node.x + this.nodeRadius);
      maxY = Math.max(maxY, node.y + this.nodeRadius);
      if (node.children) {
        for (const child of node.children) computeBounds(child);
      }
    };
    computeBounds(rootNode);

    return {
      root: rootNode,
      width: Math.max(maxX - minX + 80, 500),
      height: Math.max(maxY + 80, 420),
      minX: minX - 40
    };
  }
}

// ==============================================================================
// SVG PARSE TREE RENDERER
// ==============================================================================

class TreeSVGRenderer {
  constructor(svgElementId, containerElementId) {
    this.svg = document.getElementById(svgElementId);
    this.container = document.getElementById(containerElementId);
    this.layoutEngine = new TreeLayoutEngine();
    this.currentTree = null;
    this.layoutResult = null;
    this.transform = { x: 0, y: 0, k: 1 };
    this.highlightedNodeId = null;

    if (this.svg && this.container) {
      this.initInteractions();
    }
  }

  initInteractions() {
    let isPanning = false;
    let startPos = { x: 0, y: 0 };

    this.container.addEventListener("mousedown", (e) => {
      // Avoid panning when clicking inside tooltip or button
      if (e.target.closest("button") || e.target.closest(".tree-legend")) return;
      isPanning = true;
      startPos = { x: e.clientX - this.transform.x, y: e.clientY - this.transform.y };
      this.container.style.cursor = "grabbing";
    });

    window.addEventListener("mousemove", (e) => {
      if (!isPanning) return;
      this.transform.x = e.clientX - startPos.x;
      this.transform.y = e.clientY - startPos.y;
      this.applyTransform();
    });

    window.addEventListener("mouseup", () => {
      if (isPanning) {
        isPanning = false;
        this.container.style.cursor = "grab";
      }
    });

    this.container.addEventListener("wheel", (e) => {
      e.preventDefault();
      const zoomFactor = e.deltaY < 0 ? 1.12 : 0.88;
      const newScale = Math.min(Math.max(this.transform.k * zoomFactor, 0.3), 3.0);
      
      const rect = this.container.getBoundingClientRect();
      const mouseX = e.clientX - rect.left;
      const mouseY = e.clientY - rect.top;

      this.transform.x = mouseX - (mouseX - this.transform.x) * (newScale / this.transform.k);
      this.transform.y = mouseY - (mouseY - this.transform.y) * (newScale / this.transform.k);
      this.transform.k = newScale;
      this.applyTransform();
    }, { passive: false });
  }

  applyTransform() {
    const mainGroup = this.svg.querySelector(".tree-main-group");
    if (mainGroup) {
      mainGroup.setAttribute(
        "transform",
        `translate(${this.transform.x}, ${this.transform.y}) scale(${this.transform.k})`
      );
    }
  }

  zoom(factor) {
    const newScale = Math.min(Math.max(this.transform.k * factor, 0.3), 3.0);
    const rect = this.container.getBoundingClientRect();
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;

    this.transform.x = centerX - (centerX - this.transform.x) * (newScale / this.transform.k);
    this.transform.y = centerY - (centerY - this.transform.y) * (newScale / this.transform.k);
    this.transform.k = newScale;
    this.applyTransform();
  }

  resetView() {
    if (!this.layoutResult) return;
    const rect = this.container.getBoundingClientRect();
    const padding = 50;

    const scaleX = (rect.width - padding * 2) / this.layoutResult.width;
    const scaleY = (rect.height - padding * 2) / this.layoutResult.height;
    const scale = Math.min(scaleX, scaleY, 1.1);

    this.transform.k = scale;
    this.transform.x = (rect.width - this.layoutResult.width * scale) / 2 - (this.layoutResult.minX * scale);
    this.transform.y = 25;
    this.applyTransform();
  }

  render(treeData, visibleNodeIds = null) {
    if (!this.svg) return;
    this.currentTree = JSON.parse(JSON.stringify(treeData));
    this.layoutResult = this.layoutEngine.layout(this.currentTree);

    this.svg.innerHTML = "";

    const mainGroup = document.createElementNS("http://www.w3.org/2000/svg", "g");
    mainGroup.setAttribute("class", "tree-main-group");
    this.svg.appendChild(mainGroup);

    // Group for edges
    const edgesGroup = document.createElementNS("http://www.w3.org/2000/svg", "g");
    edgesGroup.setAttribute("class", "edges-layer");
    mainGroup.appendChild(edgesGroup);

    // Group for nodes
    const nodesGroup = document.createElementNS("http://www.w3.org/2000/svg", "g");
    nodesGroup.setAttribute("class", "nodes-layer");
    mainGroup.appendChild(nodesGroup);

    // Recursive render helper
    const drawElements = (node) => {
      const isVisible = !visibleNodeIds || visibleNodeIds.has(node.id);

      if (node.children && isVisible) {
        for (const child of node.children) {
          const childVisible = !visibleNodeIds || visibleNodeIds.has(child.id);
          if (childVisible) {
            // Draw connector curve
            const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
            const midY = (node.y + child.y) / 2;
            const d = `M ${node.x} ${node.y} C ${node.x} ${midY}, ${child.x} ${midY}, ${child.x} ${child.y}`;
            path.setAttribute("d", d);
            path.setAttribute("class", "tree-edge");
            path.setAttribute("id", `edge-${node.id}-${child.id}`);
            edgesGroup.appendChild(path);
          }
          drawElements(child);
        }
      }

      if (isVisible) {
        // Draw Node
        const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
        g.setAttribute("class", `node-group ${node.is_terminal ? "node-terminal" : "node-nonterminal"}`);
        g.setAttribute("id", `node-${node.id}`);
        g.setAttribute("transform", `translate(${node.x}, ${node.y})`);

        if (node.is_terminal) {
          // Terminal: Rounded rectangle
          const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
          const w = Math.max(node.label.length * 10 + 20, 36);
          const h = 32;
          rect.setAttribute("x", -w / 2);
          rect.setAttribute("y", -h / 2);
          rect.setAttribute("width", w);
          rect.setAttribute("height", h);
          g.appendChild(rect);
        } else {
          // Nonterminal: Circular badge
          const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
          circle.setAttribute("r", 20);
          g.appendChild(circle);
        }

        const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
        text.textContent = node.label;
        g.appendChild(text);

        // Tooltip title
        const title = document.createElementNS("http://www.w3.org/2000/svg", "title");
        title.textContent = `${node.is_terminal ? "Terminal" : "Non-Terminal"}: ${node.label}\n${node.rule ? "Production: " + node.rule : ""}`;
        g.appendChild(title);

        nodesGroup.appendChild(g);
      }
    };

    drawElements(this.layoutResult.root);
    this.resetView();
  }

  highlightNode(nodeId) {
    if (this.highlightedNodeId) {
      const oldNode = this.svg.querySelector(`#node-${this.highlightedNodeId}`);
      if (oldNode) oldNode.classList.remove("active");
    }
    this.highlightedNodeId = nodeId;
    if (nodeId) {
      const newNode = this.svg.querySelector(`#node-${nodeId}`);
      if (newNode) newNode.classList.add("active");
    }
  }

  exportSVG() {
    if (!this.svg) return;
    const serializer = new XMLSerializer();
    const source = serializer.serializeToString(this.svg);
    const blob = new Blob([source], { type: "image/svg+xml;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `parse_tree_${Date.now()}.svg`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }
}

// Global SVG Renderer instance for Simulator page
let simulatorRenderer = null;
let comparisonRendererAmb = null;
let comparisonRendererUnamb = null;

// ==============================================================================
// SIMULATION ENGINE & PLAYBACK CONTROLLER
// ==============================================================================

class SimulationController {
  constructor() {
    this.steps = [];
    this.currentIndex = 0;
    this.isPlaying = false;
    this.timer = null;
    this.speedMs = 1000;
  }

  loadSimulation(data) {
    this.stopPlayback();
    this.data = data;
    this.steps = data.steps || [];
    this.currentIndex = 0;
    this.updateUI();
  }

  setSpeed(speedVal) {
    this.speedMs = Math.round(1000 / parseFloat(speedVal));
    if (this.isPlaying) {
      this.stopPlayback();
      this.startPlayback();
    }
  }

  nextStep() {
    if (this.currentIndex < this.steps.length - 1) {
      this.currentIndex++;
      this.updateUI();
    } else {
      this.stopPlayback();
    }
  }

  prevStep() {
    if (this.currentIndex > 0) {
      this.currentIndex--;
      this.updateUI();
    }
  }

  reset() {
    this.stopPlayback();
    this.currentIndex = 0;
    this.updateUI();
  }

  togglePlayback() {
    if (this.isPlaying) {
      this.stopPlayback();
    } else {
      if (this.currentIndex >= this.steps.length - 1) {
        this.currentIndex = 0;
      }
      this.startPlayback();
    }
  }

  startPlayback() {
    this.isPlaying = true;
    const playBtn = document.getElementById("btnPlayPause");
    if (playBtn) {
      playBtn.innerHTML = '<i class="bi bi-pause-fill"></i> Pause';
      playBtn.classList.replace("btn-primary", "btn-accent");
    }
    this.timer = setInterval(() => {
      if (this.currentIndex < this.steps.length - 1) {
        this.nextStep();
      } else {
        this.stopPlayback();
      }
    }, this.speedMs);
  }

  stopPlayback() {
    this.isPlaying = false;
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = null;
    }
    const playBtn = document.getElementById("btnPlayPause");
    if (playBtn) {
      playBtn.innerHTML = '<i class="bi bi-play-fill"></i> Play';
      playBtn.classList.replace("btn-accent", "btn-primary");
    }
  }

  updateUI() {
    const totalSteps = this.steps.length;
    const currentStep = this.steps[this.currentIndex];

    // Progress bar
    const progressFill = document.getElementById("progressFill");
    const progressPercent = totalSteps > 1 ? (this.currentIndex / (totalSteps - 1)) * 100 : 100;
    if (progressFill) progressFill.style.width = `${progressPercent}%`;

    // Step counter
    const stepBadge = document.getElementById("stepCounterBadge");
    if (stepBadge) {
      stepBadge.textContent = totalSteps > 0 ? `Step ${this.currentIndex + 1} of ${totalSteps}` : "Step 0";
    }

    if (!currentStep) return;

    // Step details card
    const titleEl = document.getElementById("stepActionTitle");
    const ruleEl = document.getElementById("stepRuleBadge");
    const explanationEl = document.getElementById("stepExplanation");
    const lookaheadEl = document.getElementById("stepLookahead");
    const remainingEl = document.getElementById("stepRemainingInput");
    const stackEl = document.getElementById("stepStack");

    if (titleEl) titleEl.textContent = currentStep.action;
    if (ruleEl) {
      ruleEl.textContent = currentStep.rule || "Direct Parsing Action";
      ruleEl.style.display = currentStep.rule ? "inline-block" : "none";
    }
    if (explanationEl) explanationEl.textContent = currentStep.explanation;
    if (lookaheadEl) lookaheadEl.textContent = currentStep.lookahead || "None";
    if (remainingEl) remainingEl.textContent = currentStep.remaining_input || "EOF";
    if (stackEl) stackEl.textContent = currentStep.stack ? currentStep.stack.join(" ") : "Empty";

    // Enable/Disable step buttons
    const btnPrev = document.getElementById("btnPrevStep");
    const btnNext = document.getElementById("btnNextStep");
    if (btnPrev) btnPrev.disabled = this.currentIndex === 0;
    if (btnNext) btnNext.disabled = this.currentIndex === totalSteps - 1;
  }
}

const simController = new SimulationController();

// ==============================================================================
// API CALLS AND PAGE HANDLERS
// ==============================================================================

/**
 * Triggers full simulation for the simulator page.
 */
async function runSimulator() {
  const exprInput = document.getElementById("expressionInput");
  const grammarInput = document.querySelector(".grammar-radio-card.active");
  const grammarType = grammarInput ? grammarInput.dataset.grammar : "unambiguous";

  const expression = exprInput ? exprInput.value.trim() : "id + id * id";

  if (!expression) {
    showErrorAlert("Expression cannot be empty. Please enter an expression like 'id + id * id'.");
    return;
  }

  showLoadingState();

  try {
    const res = await fetch("/api/simulate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ expression, grammar: grammarType })
    });
    const data = await res.json();

    if (!data.success) {
      showErrorAlert(data.error.message, data.error.suggestion, data.error.position);
      return;
    }

    hideErrorAlert();
    displaySimulationResults(data);
  } catch (err) {
    showErrorAlert(`Network or server error: ${err.message}`);
  }
}

/**
 * Displays simulation results in the UI.
 */
function displaySimulationResults(data) {
  State.simulationData = data;
  const resultBanner = document.getElementById("resultAlertBanner");
  const treeTabsContainer = document.getElementById("treeTabsContainer");

  // Show success result banner
  if (resultBanner) {
    resultBanner.className = "alert-banner alert-success";
    resultBanner.style.display = "flex";
    resultBanner.innerHTML = `
      <div class="alert-icon"><i class="bi bi-check-circle-fill"></i></div>
      <div class="alert-content">
        <h4>Valid Expression Accepted (${data.grammar_name})</h4>
        <p>${data.explanation}</p>
        <p style="margin-top:0.4rem; font-family:var(--font-mono); font-size:0.85rem;">
          <strong>Semantic Precedence Grouping:</strong> 
          <span style="color:var(--primary-700);">${data.grouping || (data.trees && data.trees[0] ? data.trees[0].grouping : "")}</span>
        </p>
      </div>
    `;
  }

  // Handle tree rendering based on grammar type
  if (data.grammar_type === "ambiguous") {
    // Show tabs for ambiguous trees
    if (treeTabsContainer) {
      treeTabsContainer.style.display = "flex";
      treeTabsContainer.innerHTML = data.trees.map((t, idx) => `
        <button class="tree-tab-btn ${idx === 0 ? "active" : ""}" onclick="switchAmbiguousTree(${idx})">
          Tree ${t.tree_id}: ${t.grouping}
        </button>
      `).join("");
    }
    State.activeTreeIndex = 0;
    if (data.trees && data.trees.length > 0) {
      simulatorRenderer.render(data.trees[0].tree);
      populateDerivationTables(data.trees[0].leftmost_derivation, data.trees[0].rightmost_derivation);
    }
  } else {
    // Single unambiguous tree
    if (treeTabsContainer) {
      treeTabsContainer.style.display = "none";
    }
    simulatorRenderer.render(data.tree);
    populateDerivationTables(data.leftmost_derivation, data.rightmost_derivation);
  }

  // Load steps into simulation controller
  simController.loadSimulation(data);
}

/**
 * Switches between multiple parse trees under ambiguous grammar.
 */
function switchAmbiguousTree(index) {
  if (!State.simulationData || !State.simulationData.trees) return;
  State.activeTreeIndex = index;

  const tabs = document.querySelectorAll(".tree-tab-btn");
  tabs.forEach((tab, i) => {
    tab.classList.toggle("active", i === index);
  });

  const selectedTreeObj = State.simulationData.trees[index];
  if (selectedTreeObj) {
    simulatorRenderer.render(selectedTreeObj.tree);
    populateDerivationTables(selectedTreeObj.leftmost_derivation, selectedTreeObj.rightmost_derivation);
  }
}

/**
 * Populates Leftmost and Rightmost Derivation tables.
 */
function populateDerivationTables(lmdSteps, rmdSteps) {
  const lmdBody = document.getElementById("lmdTableBody");
  const rmdBody = document.getElementById("rmdTableBody");

  if (lmdBody && lmdSteps) {
    lmdBody.innerHTML = lmdSteps.map(s => `
      <tr>
        <td style="width:50px;">${s.step_num}</td>
        <td style="color:var(--primary-700); font-weight:700;">${s.sentential_form}</td>
        <td style="color:var(--slate-600);">${s.rule_applied}</td>
      </tr>
    `).join("");
  }

  if (rmdBody && rmdSteps) {
    rmdBody.innerHTML = rmdSteps.map(s => `
      <tr>
        <td style="width:50px;">${s.step_num}</td>
        <td style="color:var(--primary-700); font-weight:700;">${s.sentential_form}</td>
        <td style="color:var(--slate-600);">${s.rule_applied}</td>
      </tr>
    `).join("");
  }
}

/**
 * Executes side-by-side comparison.
 */
async function runComparison() {
  const exprInput = document.getElementById("comparisonExprInput");
  const expression = exprInput ? exprInput.value.trim() : "id + id * id";

  if (!expression) {
    showErrorAlert("Expression cannot be empty.");
    return;
  }

  try {
    const res = await fetch("/api/compare", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ expression })
    });
    const data = await res.json();
    State.comparisonData = data;
    displayComparisonResults(data);
  } catch (err) {
    showErrorAlert(`Comparison error: ${err.message}`);
  }
}

/**
 * Renders comparison columns and matrices.
 */
function displayComparisonResults(data) {
  const amb = data.ambiguous;
  const unamb = data.unambiguous;
  const conclusion = data.conclusion;

  // Render Ambiguous Side
  const ambCountEl = document.getElementById("ambTreeCount");
  const ambGroupingsEl = document.getElementById("ambGroupings");
  if (ambCountEl) ambCountEl.textContent = `${amb.tree_count || 0} Parse Tree${amb.tree_count === 1 ? "" : "s"}`;
  
  if (amb.success && amb.trees && amb.trees.length > 0) {
    if (ambGroupingsEl) {
      ambGroupingsEl.innerHTML = amb.trees.map((t, idx) => `
        <span class="preset-pill" style="margin-right:0.4rem;" onclick="switchComparisonAmbTree(${idx})">
          Tree ${idx + 1}: ${t.grouping}
        </span>
      `).join("");
    }
    if (comparisonRendererAmb) {
      comparisonRendererAmb.render(amb.trees[0].tree);
    }
  }

  // Render Unambiguous Side
  const unambCountEl = document.getElementById("unambTreeCount");
  const unambGroupingsEl = document.getElementById("unambGroupings");
  if (unambCountEl) unambCountEl.textContent = `${unamb.tree_count || 0} Unique Parse Tree`;
  if (unamb.success && unamb.tree) {
    if (unambGroupingsEl) {
      unambGroupingsEl.innerHTML = `<span class="preset-pill">${unamb.grouping}</span>`;
    }
    if (comparisonRendererUnamb) {
      comparisonRendererUnamb.render(unamb.tree);
    }
  }

  // Update Conclusion Card
  const conclusionSummaryEl = document.getElementById("conclusionSummaryText");
  const ambMatrixTreesEl = document.getElementById("matrixAmbTrees");
  const unambMatrixTreesEl = document.getElementById("matrixUnambTrees");

  if (conclusionSummaryEl) conclusionSummaryEl.textContent = conclusion.summary;
  if (ambMatrixTreesEl) ambMatrixTreesEl.textContent = conclusion.ambiguous_tree_count;
  if (unambMatrixTreesEl) unambMatrixTreesEl.textContent = conclusion.unambiguous_tree_count;
}

function switchComparisonAmbTree(idx) {
  if (State.comparisonData && State.comparisonData.ambiguous && State.comparisonData.ambiguous.trees) {
    const treeObj = State.comparisonData.ambiguous.trees[idx];
    if (treeObj && comparisonRendererAmb) {
      comparisonRendererAmb.render(treeObj.tree);
    }
  }
}

// Error & Alert Utilities
function showErrorAlert(message, suggestion = "", position = 0) {
  const resultBanner = document.getElementById("resultAlertBanner");
  if (resultBanner) {
    resultBanner.className = "alert-banner alert-danger";
    resultBanner.style.display = "flex";
    resultBanner.innerHTML = `
      <div class="alert-icon"><i class="bi bi-exclamation-triangle-fill"></i></div>
      <div class="alert-content">
        <h4>Syntax Error: Expression Rejected</h4>
        <p>${message}</p>
        ${suggestion ? `<p style="margin-top:0.35rem; font-size:0.85rem; color:#991b1b;"><strong>Suggestion:</strong> ${suggestion}</p>` : ""}
      </div>
    `;
  }
}

function hideErrorAlert() {
  const resultBanner = document.getElementById("resultAlertBanner");
  if (resultBanner) resultBanner.style.display = "none";
}

function showLoadingState() {
  const resultBanner = document.getElementById("resultAlertBanner");
  if (resultBanner) {
    resultBanner.className = "alert-banner alert-warning";
    resultBanner.style.display = "flex";
    resultBanner.innerHTML = `
      <div class="alert-icon"><i class="bi bi-hourglass-split"></i></div>
      <div class="alert-content">
        <h4>Parsing in progress...</h4>
        <p>Executing recursive-descent tokenization and AST construction.</p>
      </div>
    `;
  }
}

// Preset and UI Setup on Load
document.addEventListener("DOMContentLoaded", () => {
  // Initialize Simulator SVG Renderer if on simulator page
  if (document.getElementById("simulatorTreeSvg")) {
    simulatorRenderer = new TreeSVGRenderer("simulatorTreeSvg", "simulatorTreeContainer");
  }

  // Initialize Comparison SVG Renderers if on comparison page
  if (document.getElementById("comparisonAmbTreeSvg")) {
    comparisonRendererAmb = new TreeSVGRenderer("comparisonAmbTreeSvg", "comparisonAmbContainer");
  }
  if (document.getElementById("comparisonUnambTreeSvg")) {
    comparisonRendererUnamb = new TreeSVGRenderer("comparisonUnambTreeSvg", "comparisonUnambContainer");
  }

  // Simulator playback buttons
  const btnPlay = document.getElementById("btnPlayPause");
  if (btnPlay) btnPlay.addEventListener("click", () => simController.togglePlayback());

  const btnNext = document.getElementById("btnNextStep");
  if (btnNext) btnNext.addEventListener("click", () => simController.nextStep());

  const btnPrev = document.getElementById("btnPrevStep");
  if (btnPrev) btnPrev.addEventListener("click", () => simController.prevStep());

  const btnReset = document.getElementById("btnResetSteps");
  if (btnReset) btnReset.addEventListener("click", () => simController.reset());

  const speedSelect = document.getElementById("playbackSpeedSelect");
  if (speedSelect) {
    speedSelect.addEventListener("change", (e) => simController.setSpeed(e.target.value));
  }

  // Zoom buttons
  const btnZoomIn = document.getElementById("btnZoomIn");
  if (btnZoomIn) btnZoomIn.addEventListener("click", () => simulatorRenderer && simulatorRenderer.zoom(1.2));

  const btnZoomOut = document.getElementById("btnZoomOut");
  if (btnZoomOut) btnZoomOut.addEventListener("click", () => simulatorRenderer && simulatorRenderer.zoom(0.8));

  const btnResetZoom = document.getElementById("btnResetZoom");
  if (btnResetZoom) btnResetZoom.addEventListener("click", () => simulatorRenderer && simulatorRenderer.resetView());

  const btnExport = document.getElementById("btnExportSvg");
  if (btnExport) btnExport.addEventListener("click", () => simulatorRenderer && simulatorRenderer.exportSVG());

  // Grammar Radio Selector Cards
  const grammarCards = document.querySelectorAll(".grammar-radio-card");
  grammarCards.forEach(card => {
    card.addEventListener("click", () => {
      grammarCards.forEach(c => c.classList.remove("active"));
      card.classList.add("active");
      const selectedGrammar = card.dataset.grammar;
      State.currentGrammar = selectedGrammar;

      // Update rules display box
      const rulesAmb = document.getElementById("rulesDisplayAmbiguous");
      const rulesUnamb = document.getElementById("rulesDisplayUnambiguous");
      if (rulesAmb && rulesUnamb) {
        if (selectedGrammar === "ambiguous") {
          rulesAmb.style.display = "block";
          rulesUnamb.style.display = "none";
        } else {
          rulesAmb.style.display = "none";
          rulesUnamb.style.display = "block";
        }
      }
    });
  });

  // Preset pill clicks
  document.querySelectorAll(".preset-pill").forEach(pill => {
    pill.addEventListener("click", () => {
      const expr = pill.dataset.expr || pill.textContent.trim();
      const simInput = document.getElementById("expressionInput");
      const compInput = document.getElementById("comparisonExprInput");
      if (simInput) {
        simInput.value = expr;
        runSimulator();
      }
      if (compInput) {
        compInput.value = expr;
        runComparison();
      }
    });
  });

  // Tab navigation for Derivations
  document.querySelectorAll(".tab-nav-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const tabTarget = btn.dataset.tab;
      document.querySelectorAll(".tab-nav-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");

      document.querySelectorAll(".tab-content-panel").forEach(panel => {
        panel.style.display = panel.id === tabTarget ? "block" : "none";
      });
    });
  });

  // Auto-run default simulation on load if element exists
  if (document.getElementById("expressionInput")) {
    runSimulator();
  }
  if (document.getElementById("comparisonExprInput")) {
    runComparison();
  }
});
