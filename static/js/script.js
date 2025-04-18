document.addEventListener("DOMContentLoaded", () => {
  // Mobile menu toggle
  const mobileMenuToggle = document.getElementById("mobileMenuToggle")
  const sidebar = document.querySelector(".sidebar")

  if (mobileMenuToggle) {
    mobileMenuToggle.addEventListener("click", () => {
      sidebar.classList.toggle("active")
    })

    // Close sidebar when clicking outside on mobile
    document.addEventListener("click", (e) => {
      if (
        window.innerWidth <= 768 &&
        sidebar.classList.contains("active") &&
        !sidebar.contains(e.target) &&
        e.target !== mobileMenuToggle
      ) {
        sidebar.classList.remove("active")
      }
    })
  }

  // Toggle sidebar collapse
  const toggleSidebarBtn = document.getElementById("toggleSidebar")
  const mainContent = document.getElementById("mainContent")

  if (toggleSidebarBtn) {
    toggleSidebarBtn.addEventListener("click", () => {
      sidebar.classList.toggle("collapsed")
      mainContent.classList.toggle("expanded")

      // Store sidebar state in localStorage
      localStorage.setItem("sidebarCollapsed", sidebar.classList.contains("collapsed"))
    })

    // Check if sidebar was collapsed previously
    const sidebarCollapsed = localStorage.getItem("sidebarCollapsed") === "true"
    if (sidebarCollapsed) {
      sidebar.classList.add("collapsed")
      mainContent.classList.add("expanded")
    }
  }

  // Theme toggle
  const themeToggle = document.getElementById("themeToggle")
  const themeIcon = document.getElementById("themeIcon")
  const body = document.body

  if (themeToggle) {
    themeToggle.addEventListener("click", () => {
      body.classList.toggle("light-theme")

      if (body.classList.contains("light-theme")) {
        themeIcon.textContent = "light_mode"
        localStorage.setItem("theme", "light")
      } else {
        themeIcon.textContent = "dark_mode"
        localStorage.setItem("theme", "dark")
      }

      showToast("info", "Theme Changed", body.classList.contains("light-theme") ? "Light theme applied" : "Dark theme applied")
    })

    // Apply saved theme on load
    const savedTheme = localStorage.getItem("theme") || "dark"
    if (savedTheme === "light") {
      body.classList.add("light-theme")
      themeIcon.textContent = "light_mode"
    }
  }

  // Navigation
  const navItems = document.querySelectorAll(".nav-item")
  const pages = document.querySelectorAll(".page")
  const pageTitle = document.querySelector(".page-title")

  navItems.forEach((item) => {
    item.addEventListener("click", function (e) {
      e.preventDefault()
      showPage(this.dataset.page)
    })
  })

  // Function to update statistics with animation
  function updateStats() {
    fetch("/api/stats")
      .then((response) => response.json())
      .then((data) => {
        animateNumber("reports-count", data.reports_count)
        animateNumber("modules-count", data.modules_count)
        animateNumber("clients-count", data.clients_count)
      })
      .catch((error) => {
        console.error("Error fetching stats:", error)
        // Fallback values
        animateNumber("reports-count", 0)
        animateNumber("modules-count", 0)
        animateNumber("clients-count", 0)
        showToast("error", "Error", "Failed to update statistics")
      })
  }

  // Function to animate numbers
  function animateNumber(elementId, final) {
    const element = document.getElementById(elementId)
    if (!element) return

    const start = Number.parseInt(element.textContent) || 0
    const duration = 1500
    const step = (final - start) / (duration / 16)
    let current = start

    function animate() {
      current += step
      if ((step > 0 && current >= final) || (step < 0 && current <= final)) {
        element.textContent = final
      } else {
        element.textContent = Math.round(current)
        requestAnimationFrame(animate)
      }
    }

    animate()
  }

  // Function to update recent scans
  function updateRecentScans() {
    fetch("/api/recent-scans")
      .then((response) => response.json())
      .then((scans) => {
        const scansList = document.getElementById("recent-scans-list")
        if (scans.length === 0) {
          scansList.innerHTML = `
            <div class="empty-state">
              <p>No recent scans found</p>
            </div>
          `
        } else {
          scansList.innerHTML = scans
            .map(
              (scan) => `
                <div class="scan-item">
                  <div class="scan-info">
                    <div class="scan-target">${scan.target}</div>
                    <div class="scan-date">${formatDate(scan.date)}</div>
                  </div>
                  <div class="scan-status ${scan.status.toLowerCase()}">${scan.status}</div>
                </div>
              `,
            )
            .join("")
        }
      })
      .catch((error) => {
        console.error("Error fetching recent scans:", error)
        // Fallback for demo
        const demoScans = [
          { target: "example.com", date: "2023-05-15T12:30:00", status: "completed" },
          { target: "https://liquidterroir.net/", date: "2023-05-14T15:45:00", status: "completed" },
          { target: "liquidterroir.net", date: "2023-05-13T10:15:00", status: "completed" }
        ]

        const scansList = document.getElementById("recent-scans-list")
        scansList.innerHTML = demoScans
          .map(
            (scan) => `
              <div class="scan-item">
                <div class="scan-info">
                  <div class="scan-target">${scan.target}</div>
                  <div class="scan-date">${formatDate(scan.date)}</div>
                </div>
                <div class="scan-status ${scan.status.toLowerCase()}">${scan.status}</div>
              </div>
            `,
          )
          .join("")
      })
  }

  // Format date helper
  function formatDate(dateString) {
    const date = new Date(dateString)
    return date.toLocaleString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    })
  }

  // Scan console
  const scanConsole = {
    element: document.getElementById("scan-console"),
    output: document.getElementById("console-output"),
    addMessage(message) {
      const line = document.createElement("div")
      line.textContent = message
      this.output.appendChild(line)
      this.element.scrollTop = this.element.scrollHeight
    },
    clear() {
      this.output.innerHTML = ""
    },
  }

  // Project scan console
  const projectScanConsole = {
    element: document.getElementById("project-scan-console"),
    output: document.getElementById("project-console-output"),
    addMessage(message) {
      const line = document.createElement("div")
      line.textContent = message
      this.output.appendChild(line)
      this.element.scrollTop = this.element.scrollHeight
    },
    clear() {
      this.output.innerHTML = ""
    },
  }

  const stopScanBtn = document.getElementById("stopScanBtn")
  if (stopScanBtn) {
    stopScanBtn.addEventListener("click", async () => {
      try {
        const response = await fetch("/stopscan", { method: "POST" })
        const data = await response.json()

        if (response.status === 200) {
          scanConsole.addMessage(data.message || "[*] Scan stopped successfully")
          showToast("warning", "Scan Aborted", "The scan has been stopped")
        } else if (response.status === 404) {
          scanConsole.addMessage(data.message || "[*] No scan is running")
          showToast("warning", "No Scan Running", data.message)
        } else {
          scanConsole.addMessage(data.error || "[!] Error: Failed to stop the scan")
          showToast("error", "Error", data.error || "Failed to stop the scan")
        }
      } catch (error) {
        console.error("Error stopping scan:", error)
        scanConsole.addMessage("[!] Error: Failed to stop the scan")
        showToast("error", "Error", "Failed to stop the scan")
      }
    })
  }

  const clearConsoleBtn = document.getElementById("clearConsoleBtn")
  if (clearConsoleBtn) {
    clearConsoleBtn.addEventListener("click", () => {
      scanConsole.clear()
      showToast("info", "Console Cleared", "The scan console has been cleared")
    })
  }

  // Project scan buttons
  const stopProjectScanBtn = document.getElementById("stopProjectScanBtn")
  if (stopProjectScanBtn) {
    stopProjectScanBtn.addEventListener("click", async () => {
      try {
        const response = await fetch("/stopscan", { method: "POST" })
        const data = await response.json()

        if (response.status === 200) {
          projectScanConsole.addMessage(data.message || "[*] Scan stopped successfully")
          showToast("warning", "Scan Aborted", "The Scan has been stopped")
        } else if (response.status === 404) {
          projectScanConsole.addMessage(data.message || "[*] No scan is running")
          showToast("warning", "No Scan Running", data.message)
        } else {
          projectScanConsole.addMessage(data.error || "[!] Error: Failed to stop the scan")
          showToast("error", "Error", data.error || "Failed to stop the scan")
        }
      } catch (error) {
        console.error("Error stopping scan:", error)
        projectScanConsole.addMessage("[!] Error: Failed to stop the scan")
        showToast("error", "Error", "Failed to stop the scan")
      }
    })
  }

  const clearProjectConsoleBtn = document.getElementById("clearProjectConsoleBtn")
  if (clearProjectConsoleBtn) {
    clearProjectConsoleBtn.addEventListener("click", () => {
      projectScanConsole.clear()
      showToast("info", "Console Cleared", "The scan console has been cleared")
    })
  }

  // Function to start a full scan
  async function startFullScan(event) {
    event.preventDefault()
    const form = event.target
    const formData = new FormData(form)
    const target = formData.get("target")
    const isComprehensive = document.getElementById("comprehensiveScan").checked

    document.getElementById("fullScanTarget").value = ""
    scanConsole.clear()
    scanConsole.addMessage(`[*] Starting full scan for ${target}...`)
    showToast("info", "Scan Started", `Starting full scan for ${target}`)

    if (isComprehensive) {
      formData.append("comprehensive", "true")
    }

    try {
      const response = await fetch("/fullscan", {
        method: "POST",
        body: formData,
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let done = false

      while (!done) {
        const { value, done: doneReading } = await reader.read()
        done = doneReading
        if (value) {
          const chunk = decoder.decode(value, { stream: true })
          // Split the chunk into lines and add each line to the console
          const lines = chunk.split("\n")
          lines.forEach((line) => {
            if (line.trim() !== "") {
              scanConsole.addMessage(line)
            }
          })
        }
      }

      showToast("success", "Scan Completed", `Scan for ${target} has finished`)
      updateRecentScans()
      updateStats()
    } catch (error) {
      console.error("Error during scan:", error)
      scanConsole.addMessage(`[!] Error: ${error.message}`)
      showToast("error", "Scan Error", "An error occurred during the scan")

    }
  }

  // Function to start a project scan
  async function startProjectScan() {
    const target = document.getElementById("scan-target").textContent
    const isComprehensive = document.getElementById("projectComprehensiveScan").checked
    const formData = new FormData()
    formData.append("target", target)
    formData.append("scanType", "project")

    if (isComprehensive) {
      formData.append("comprehensive", "true")
    }

    projectScanConsole.clear()
    projectScanConsole.addMessage(`[*] Starting full scan for ${target}...`)
    showToast("info", "Scan Started", `Starting scan for project target: ${target}`)

    try {
      const response = await fetch("/fullscan", {
        method: "POST",
        body: formData,
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let done = false

      while (!done) {
        const { value, done: doneReading } = await reader.read()
        done = doneReading
        if (value) {
          const chunk = decoder.decode(value, { stream: true })
          // Split the chunk into lines and add each line to the console
          const lines = chunk.split("\n")
          lines.forEach((line) => {
            if (line.trim() !== "") {
              projectScanConsole.addMessage(line)
            }
          })
        }
      }

      showToast("success", "Scan Completed", `Scan for ${target} has finished`)

      // Refresh project reports if we're on the reports tab
      if (document.querySelector('.tab-btn[data-tab="reports"]').classList.contains("active")) {
        loadProjectReports(currentProject.id)
      }
    } catch (error) {
      console.error("Error during scan:", error)
      projectScanConsole.addMessage(`[!] Error: ${error.message}`)
      showToast("error", "Scan Error", "An error occurred during the scan")
    }
  }

  // Handle full scan form submission
  const fullScanForm = document.getElementById("fullScanForm")
  if (fullScanForm) {
    fullScanForm.addEventListener("submit", startFullScan)
  }

  // Handle project scan button
  const startProjectScanBtn = document.getElementById("startProjectScanBtn")
  if (startProjectScanBtn) {
    startProjectScanBtn.addEventListener("click", startProjectScan)
  }

  // Load reports
  function loadReports() {
    const reportsContainer = document.getElementById("reports-container")
    if (!reportsContainer) return

    reportsContainer.innerHTML = `
      <div class="skeleton-loader">
        <div class="skeleton-item"></div>
        <div class="skeleton-item"></div>
        <div class="skeleton-item"></div>
      </div>
    `

    fetch("/api/reports")
      .then((response) => response.json())
      .then((reports) => {
        if (reports.length === 0) {
          reportsContainer.innerHTML = `
            <div class="empty-state">
              <h2>No Reports Found</h2>
              <p>Run a scan to generate security reports.</p>
            </div>
          `
        } else {
          reportsContainer.innerHTML = reports
            .map(
              (report) => `
                <div class="report-card">
                  <div class="report-preview-container" onclick="window.open('/report/${report.filename}', '_blank')">
                    <span class="material-icons-round report-icon">description</span>
                    <div class="report-view-overlay">
                      <span class="material-icons-round">visibility</span>
                    </div>
                  </div>
                  <div class="report-info">
                    <div class="report-title">
                      ${report.filename.length > 20 ? report.filename.substring(0, 16) + "....pdf" : report.filename}
                    </div>
                    <button class="delete-report" data-filename="${report.filename}" aria-label="Delete report">
                      <span class="material-icons-round">delete</span>
                    </button>
                  </div>
                </div>
              `,
            )
            .join("")
          const deleteButtons = reportsContainer.querySelectorAll(".delete-report")
          deleteButtons.forEach((button) => {
            button.addEventListener("click", function () {
              deleteReport(this.dataset.filename)
            })
          })
        }
      })
      .catch((error) => {
        console.error("Error loading reports:", error)
      })
  }

  // Load project reports
  function loadProjectReports(projectId) {
    const projectReportsContainer = document.getElementById("project-reports-container")
    if (!projectReportsContainer) return

    projectReportsContainer.innerHTML = `
      <div class="skeleton-loader">
        <div class="skeleton-item"></div>
        <div class="skeleton-item"></div>
      </div>
    `

    fetch(`/api/projects/${projectId}/reports`)
      .then((response) => response.json())
      .then((reports) => {
        if (reports.length === 0) {
          projectReportsContainer.innerHTML = `
            <div class="empty-state">
              <p>No Reports Yet</p>
            </div>
          `
        } else {
          projectReportsContainer.innerHTML = reports
            .map(
              (report) => `
                <div class="report-card">
                  <div class="report-preview-container" onclick="window.open('/projects/${projectId}/reports/${report.filename}', '_blank')">
                    <span class="material-icons-round report-icon">description</span>
                    <div class="report-view-overlay">
                      <span class="material-icons-round">visibility</span>
                    </div>
                  </div>
                  <div class="report-info">
                    <div class="report-title">
                      ${report.filename.length > 20 ? report.filename.substring(0, 16) + "....pdf" : report.filename}
                    </div>
                    <button class="delete-report" data-filename="${report.filename}" data-project-id="${projectId}" aria-label="Delete report">
                      <span class="material-icons-round">delete</span>
                    </button>
                  </div>
                </div>
              `,
            )
            .join("")
          const deleteButtons = projectReportsContainer.querySelectorAll(".delete-report")
          deleteButtons.forEach((button) => {
            button.addEventListener("click", function () {
              deleteProjectReport(this.dataset.filename, this.dataset.projectId)
            })
          })
        }
      })
      .catch((error) => {
        console.error("Error loading project reports:", error)
      })
  }

  // Delete report
  function deleteReport(filename) {
    const sure = confirm(`Are you sure you want to delete the report ${filename}?`)
    if (sure) {
      fetch(`/api/reports/${filename}`, { method: "DELETE" })
        .then((response) => {
          if (response.ok) {
            loadReports()
            updateStats()
            showToast("success", "Report Deleted", `Report ${filename} has been deleted`)
          } else {
            showToast("error", "Error", "Failed to delete the report")
          }
        })
        .catch((error) => {
          console.error("Error:", error)
          showToast("error", "Error", "Failed to delete the report")
          // For demo, still update the UI
          loadReports()
        })
    }
  }

  // Delete project report
  function deleteProjectReport(filename, projectId) {
    const sure = confirm(`Are you sure you want to delete the report ${filename}?`)
    if (sure) {
      fetch(`/api/projects/${projectId}/reports/${filename}`, { method: "DELETE" })
        .then((response) => {
          if (response.ok) {
            loadProjectReports(projectId)
            showToast("success", "Report Deleted", `Report ${filename} has been deleted`)
          } else {
            showToast("error", "Error", "Failed to delete the report")
          }
        })
        .catch((error) => {
          console.error("Error:", error)
          showToast("error", "Error", "Failed to delete the report")
          // For demo, still update the UI
          loadProjectReports(projectId)
        })
    }
  }

  // Projects functionality
  let projects = []
  let currentProject = null

  // Load projects
  function loadProjects() {
    const projectsGrid = document.getElementById("projects-grid")
    if (!projectsGrid) return

    projectsGrid.innerHTML = `
      <div class="skeleton-loader">
        <div class="skeleton-item"></div>
        <div class="skeleton-item"></div>
        <div class="skeleton-item"></div>
      </div>
    `

    fetch("/api/projects")
      .then((response) => response.json())
      .then((data) => {
        projects = data
        renderProjects()
      })
      .catch((error) => {
        console.error("Error loading projects:", error)
      })
  }

  // Render projects list
  function renderProjects() {
    const projectsGrid = document.getElementById("projects-grid")
    if (!projectsGrid) return

    if (projects.length === 0) {
      projectsGrid.innerHTML = `
        <div class="empty-state">
          <p>No projects yet. Create your first project.</p>
        </div>
      `
    } else {
      projectsGrid.innerHTML = projects
        .map(
          (project) => `
            <div class="project-card ${currentProject && currentProject.id === project.id ? "active" : ""}" data-project-id="${project.id}">
              <div class="project-card-header">
                <div class="project-card-title">${project.name}</div>
                <div class="project-card-actions">
                  <button class="project-card-action delete" data-project-id="${project.id}" aria-label="Delete project">
                    <span class="material-icons-round">delete</span>
                  </button>
                </div>
              </div>
              <div class="project-card-content">
                <div class="project-card-target">
                  <span class="project-card-target-label">Target:</span>
                  <span class="project-card-target-value" title="${project.target}">${truncateUrl(project.target)}</span>
                </div>
                <div class="project-card-date">Created: ${project.created_at}</div>
              </div>
            </div>
          `,
        )
        .join("")

      // Add event listeners to project cards
      document.querySelectorAll(".project-card").forEach((card) => {
        card.addEventListener("click", function (e) {
          if (!e.target.closest('.project-card-action')) {
            const projectId = this.dataset.projectId
            selectProject(projectId)
          }
        })
      })

      // Add event listeners to delete buttons
      document.querySelectorAll(".project-card-action.delete").forEach((button) => {
        button.addEventListener("click", function (e) {
          e.stopPropagation()
          const projectId = this.dataset.projectId
          deleteProject(projectId)
        })
      })
    }
  }

  // Select a project
  function selectProject(projectId) {
    currentProject = projects.find((p) => p.id === projectId)
    if (!currentProject) return

    // Hide projects grid and show project details
    document.getElementById("projects-grid").style.display = "none"
    document.getElementById("project-details").style.display = "block"

    // Update project details
    document.getElementById("project-name").textContent = currentProject.name
    document.getElementById("scan-target").textContent = currentProject.target
    document.getElementById("project-target-display").textContent = currentProject.target

    // Reset to scanner tab
    document.querySelectorAll(".tab-btn").forEach((btn) => btn.classList.remove("active"))
    document.querySelectorAll(".tab-pane").forEach((pane) => pane.classList.remove("active"))
    document.querySelector('.tab-btn[data-tab="scanner"]').classList.add("active")
    document.getElementById("scanner-tab").classList.add("active")

    // Load project reports
    loadProjectReports(currentProject.id)
  }

  // Back to projects list
  const backToProjectsBtn = document.getElementById("backToProjectsBtn")
  if (backToProjectsBtn) {
    backToProjectsBtn.addEventListener("click", () => {
      document.getElementById("projects-grid").style.display = "grid"
      document.getElementById("project-details").style.display = "none"
    })
  }

  // Create a new project
  function createProject(name, target) {
    showToast("info", "Creating Project", "Creating new project...")

    fetch("/api/projects", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ name, target }),
    })
      .then((response) => response.json())
      .then((data) => {
        projects.push(data)
        renderProjects()
        closeModal()
        showToast("success", "Project Created", `Project "${name}" has been created`)
      })
      .catch((error) => {
        console.error("Error creating project:", error)
      })
  }

  // Delete a project
  function deleteProject(projectId) {
    const sure = confirm("Are you sure you want to delete this project?")
    if (!sure) return

    showToast("info", "Deleting Project", "Deleting project...")

    fetch(`/api/projects/${projectId}`, {
      method: "DELETE",
    })
      .then((response) => {
        if (response.ok) {
          const deletedProject = projects.find((p) => p.id === projectId)
          projects = projects.filter((p) => p.id !== projectId)
          renderProjects()

          // If we're viewing the deleted project, go back to the projects list
          if (currentProject && currentProject.id === projectId) {
            document.getElementById("projects-grid").style.display = "grid"
            document.getElementById("project-details").style.display = "none"
            currentProject = null
          }

          showToast("success", "Project Deleted", `Project "${deletedProject?.name || ""}" has been deleted`)
        } else {
          showToast("error", "Error", "Failed to delete the project")
        }
      })
      .catch((error) => {
        console.error("Error deleting project:", error)
        // Fallback for demo if API doesn't exist yet
        const deletedProject = projects.find((p) => p.id === projectId)
        projects = projects.filter((p) => p.id !== projectId)
        renderProjects()

        // If we're viewing the deleted project, go back to the projects list
        if (currentProject && currentProject.id === projectId) {
          document.getElementById("projects-grid").style.display = "grid"
          document.getElementById("project-details").style.display = "none"
          currentProject = null
        }

        showToast("success", "Project Deleted", `Project "${deletedProject?.name || ""}" has been deleted`)
      })
  }

  // Project tabs
  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", function () {
      const tabId = this.dataset.tab

      // Update active tab button
      document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"))
      this.classList.add("active")

      // Show selected tab content
      document.querySelectorAll(".tab-pane").forEach((pane) => pane.classList.remove("active"))
      document.getElementById(`${tabId}-tab`).classList.add("active")

      // Load tab-specific content if needed
      if (tabId === "reports" && currentProject) {
        loadProjectReports(currentProject.id)
      }
    })
  })

  // Modal functionality
  const modal = document.getElementById("createProjectModal")
  const createProjectForm = document.getElementById("createProjectForm")

  function openModal() {
    modal.classList.add("active")
    document.body.style.overflow = "hidden" // Prevent scrolling when modal is open
  }

  function closeModal() {
    modal.classList.remove("active")
    document.body.style.overflow = "" // Restore scrolling
    createProjectForm.reset()
  }

  // Open modal buttons
  document.getElementById("newProjectBtn").addEventListener("click", openModal)

  // Close modal
  document.querySelector(".close-modal").addEventListener("click", closeModal)
  document.querySelector(".cancel-modal-btn").addEventListener("click", closeModal)

  // Close modal when clicking on backdrop
  modal.addEventListener("click", (e) => {
    if (e.target === modal || e.target.classList.contains("modal-backdrop")) {
      closeModal()
    }
  })

  // Create project form submission
  createProjectForm.addEventListener("submit", (e) => {
    e.preventDefault()
    const name = document.getElementById("projectName").value
    const target = document.getElementById("projectTarget").value
    createProject(name, target)
  })

  // API Token Management
  function setupTokenForm(tokenName) {
    const formId = `${tokenName}TokenForm`
    const inputId = `${tokenName}Token`
    const indicatorId = `${tokenName}TokenSetIndicator`
    const statusId = `${tokenName}TokenStatus`

    const tokenForm = document.getElementById(formId)
    const tokenInput = document.getElementById(inputId)
    const tokenSetIndicator = document.getElementById(indicatorId)

    if (tokenForm && tokenInput && tokenSetIndicator) {
      // Load saved token on page load
      fetch(`/api/settings/${tokenName}-token`)
        .then((response) => response.json())
        .then((data) => {
          if (data.token) {
            tokenInput.placeholder = "••••••••••••••••••••••••••"
            tokenSetIndicator.style.display = "inline-block"
          }
        })
        .catch((error) => console.error(`Error loading ${tokenName} token:`, error))

      // Handle token form submission
      tokenForm.addEventListener("submit", async (event) => {
        event.preventDefault()
        const tokenStatus = document.getElementById(statusId)

        try {
          const response = await fetch(`/api/settings/${tokenName}-token`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ token: tokenInput.value }),
          })

          const data = await response.json()

          if (tokenStatus) {
            tokenStatus.textContent = data.message || "Token saved successfully"
            tokenStatus.className = "token-status " + (response.ok ? "success" : "error")
            tokenStatus.style.display = "block"
          }

          if (response.ok) {
            tokenInput.placeholder = "••••••••••••••••••••••••••"
            tokenInput.value = ""
            tokenSetIndicator.style.display = "inline-block"
            showToast("success", "Token Saved", `${tokenName.toUpperCase()} API token has been saved`)
          } else {
            showToast("error", "Error", `Failed to save ${tokenName.toUpperCase()} API token`)
          }

          // Clear status message after 3 seconds
          if (tokenStatus) {
            setTimeout(() => {
              tokenStatus.style.display = "none"
            }, 3000)
          }
        } catch (error) {
          console.error(`Error saving ${tokenName} token:`, error)
          if (tokenStatus) {
            tokenStatus.textContent = "An error occurred while saving the token."
            tokenStatus.className = "token-status error"
            tokenStatus.style.display = "block"
          }
          showToast("error", "Error", `Failed to save ${tokenName.toUpperCase()} API token`)
        }
      })
    }
  }

  // Chatbot functionality
  const chatInput = document.getElementById("chat-input-field")
  const sendButton = document.getElementById("send-message-btn")
  const chatMessages = document.getElementById("chat-messages")

  function sendMessage() {
    const message = chatInput.value.trim()
    if (!message) return

    // Add user message to chat
    const time = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    chatMessages.innerHTML += `
      <div class="message user-message">
        <div class="message-content">
          <p>${message}</p>
          <span class="message-time">${time}</span>
        </div>
        <div class="message-avatar">
          <span class="material-icons-round">person</span>
        </div>
      </div>
    `

    chatInput.value = ""
    chatMessages.scrollTop = chatMessages.scrollHeight

    // Simulate bot response
    setTimeout(() => {
      const botTime = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
      chatMessages.innerHTML += `
        <div class="message bot-message">
          <div class="message-avatar">
            <span class="material-icons-round">smart_toy</span>
          </div>
          <div class="message-content">
            <p>I'm sorry, the AI assistant is not fully implemented yet. This feature will be available in a future update!</p>
            <span class="message-time">${botTime}</span>
          </div>
        </div>
      `
      chatMessages.scrollTop = chatMessages.scrollHeight
    }, 1000)
  }

  if (sendButton) {
    sendButton.addEventListener("click", sendMessage)
  }

  if (chatInput) {
    chatInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter") {
        sendMessage()
      }
    })
  }

  // Truncate URLs
  function truncateUrl(url, maxLength = 20) {
    if (url.length <= maxLength) return url

    return url.substring(0, maxLength - 3) + '...'
  }

  // Project search functionality
  function setupProjectSearch() {
    const searchInput = document.getElementById("projectSearchInput")
    if (!searchInput) return

    searchInput.addEventListener("input", function() {
      const searchTerm = this.value.toLowerCase().trim()
      filterProjects(searchTerm)
    })
  }

  function filterProjects(searchTerm) {
    if (!searchTerm) {
      renderProjects() // Show all projects if search is empty
      return
    }

    const filteredProjects = projects.filter(project =>
      project.name.toLowerCase().includes(searchTerm) ||
      project.target.toLowerCase().includes(searchTerm)
    )

    const projectsGrid = document.getElementById("projects-grid")
    if (!projectsGrid) return

    if (filteredProjects.length === 0) {
      projectsGrid.innerHTML = `
        <div class="empty-state">
          <p>No projects matching "${searchTerm}" were found</p>
        </div>
      `
    } else {
      projectsGrid.innerHTML = filteredProjects
        .map(
          (project) => `
            <div class="project-card ${currentProject && currentProject.id === project.id ? "active" : ""}" data-project-id="${project.id}">
              <div class="project-card-header">
                <div class="project-card-title">${project.name}</div>
                <div class="project-card-actions">
                  <button class="project-card-action delete" data-project-id="${project.id}" aria-label="Delete project">
                    <span class="material-icons-round">delete</span>
                  </button>
                </div>
              </div>
              <div class="project-card-content">
                <div class="project-card-target">
                  <span class="project-card-target-label">Target:</span>
                  <span class="project-card-target-value" title="${project.target}">${truncateUrl(project.target)}</span>
                </div>
                <div class="project-card-date">Created: ${project.created_at}</div>
              </div>
            </div>
          `,
        )
        .join("")

      // Add event listeners to project cards
      document.querySelectorAll(".project-card").forEach((card) => {
        card.addEventListener("click", function (e) {
          if (!e.target.closest('.project-card-action')) {
            const projectId = this.dataset.projectId
            selectProject(projectId)
          }
        })
      })

      // Add event listeners to delete buttons
      document.querySelectorAll(".project-card-action.delete").forEach((button) => {
        button.addEventListener("click", function (e) {
          e.stopPropagation()
          const projectId = this.dataset.projectId
          deleteProject(projectId)
        })
      })
    }
  }

  // Toast notifications
  function showToast(type, title, message) {
    const toastContainer = document.getElementById("toastContainer")
    if (!toastContainer) return

    const toastId = Date.now()

    const toast = document.createElement("div")
    toast.className = `toast ${type}`
    toast.id = `toast-${toastId}`

    let icon
    switch (type) {
      case "success":
        icon = "check_circle"
        break
      case "error":
        icon = "error"
        break
      case "warning":
        icon = "warning"
        break
      default:
        icon = "info"
    }

    toast.innerHTML = `
      <div class="toast-icon">
        <span class="material-icons-round">${icon}</span>
      </div>
      <div class="toast-content">
        <div class="toast-title">${title}</div>
        <div class="toast-message">${message}</div>
      </div>
      <button class="toast-close" aria-label="Close notification">
        <span class="material-icons-round">close</span>
      </button>
    `

    toastContainer.appendChild(toast)

    // Add event listener to close button
    toast.querySelector(".toast-close").addEventListener("click", () => {
      toast.remove()
    })

    // Auto-remove toast after 2.5 seconds
    setTimeout(() => {
      if (document.getElementById(`toast-${toastId}`)) {
        toast.classList.add("fade-out")
        setTimeout(() => toast.remove(), 500)
      }
    }, 2500)
  }

  // Toggle API Tokens card
  const apiTokensHeader = document.querySelector(".card-header")
  if (apiTokensHeader) {
    const toggleBtn = apiTokensHeader.querySelector(".toggle-btn")
    const apiTokensContent = document.getElementById("apiTokensContent")

    if (toggleBtn && apiTokensContent) {
      toggleBtn.addEventListener("click", function () {
        const expanded = this.getAttribute("aria-expanded") === "true"
        this.setAttribute("aria-expanded", !expanded)

        if (expanded) {
          apiTokensContent.classList.remove("expanded")
          // Wait for transition to complete before hiding
          setTimeout(() => {
            apiTokensContent.style.display = "none"
          }, 300)
        } else {
          apiTokensContent.style.display = "block"
          // Small delay to ensure display:block is applied first
          setTimeout(() => {
            apiTokensContent.classList.add("expanded")
          }, 10)
        }
      })
    }
  }
  
  // Proxy Configuration
  function setupProxyConfiguration() {
    const proxyToggle = document.getElementById("proxyToggle")
    const proxyConfigForm = document.getElementById("proxyConfigForm")
    const proxyStatusIndicator = document.getElementById("proxyStatusIndicator")
    const saveProxyBtn = document.getElementById("saveProxyBtn")
    const proxyConfigStatus = document.getElementById("proxyConfigStatus")
    const proxyProtocol = document.getElementById("proxyProtocol")
    const proxyHost = document.getElementById("proxyHost")
    const proxyPort = document.getElementById("proxyPort")

    if (!proxyToggle || !proxyConfigForm) return

    // Load saved proxy configuration
    fetch("/api/settings/proxy-config")
      .then(response => response.json())
      .then(data => {
        if (data.enabled) {
          proxyToggle.checked = true
          proxyConfigForm.style.display = "block"
          proxyStatusIndicator.style.display = "inline-block"
          
          // Fill form with saved values
          proxyProtocol.value = data.protocol || "http"
          proxyHost.value = data.host || ""
          proxyPort.value = data.port || ""
        }
      })
      .catch(error => {
        console.error("Error loading proxy configuration:", error)
      })

    // Toggle proxy configuration form
    proxyToggle.addEventListener("change", function() {
      if (this.checked) {
        proxyConfigForm.style.display = "block"
      } else {
        proxyConfigForm.style.display = "none"
        proxyStatusIndicator.style.display = "none"
        
        // If proxy is disabled, clear the configuration
        fetch("/api/settings/proxy-config", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ enabled: false }),
        })
        .then(response => response.json())
        .then(data => {
          if (proxyConfigStatus) {
            proxyConfigStatus.textContent = "Proxy disabled successfully"
            proxyConfigStatus.className = "token-status success"
            proxyConfigStatus.style.display = "block"
            
            setTimeout(() => {
              proxyConfigStatus.style.display = "none"
            }, 3000)
          }
          showToast("info", "Proxy Disabled", "Proxy configuration has been disabled")
        })
        .catch(error => {
          console.error("Error disabling proxy:", error)
          showToast("error", "Error", "Failed to disable proxy configuration")
        })
      }
    })

    // Save proxy configuration
    if (saveProxyBtn) {
      saveProxyBtn.addEventListener("click", function() {
        const protocol = proxyProtocol.value
        const host = proxyHost.value.trim()
        const port = proxyPort.value.trim()
        
        if (!host) {
          showToast("error", "Validation Error", "IP address is required")
          return
        }
        
        if (!port) {
          showToast("error", "Validation Error", "Port number is required")
          return
        }
        
        const proxyConfig = {
          enabled: true,
          protocol,
          host,
          port
        }
        
        fetch("/api/settings/proxy-config", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(proxyConfig),
        })
        .then(response => response.json())
        .then(data => {
          if (proxyConfigStatus) {
            proxyConfigStatus.textContent = data.message || "Proxy configuration saved successfully"
            proxyConfigStatus.className = "token-status success"
            proxyConfigStatus.style.display = "block"
            
            setTimeout(() => {
              proxyConfigStatus.style.display = "none"
            }, 3000)
          }
          
          proxyStatusIndicator.style.display = "inline-block"
          showToast("success", "Proxy Configured", "Proxy configuration has been saved")
        })
        .catch(error => {
          console.error("Error saving proxy configuration:", error)
          
          if (proxyConfigStatus) {
            proxyConfigStatus.textContent = "An error occurred while saving the proxy configuration."
            proxyConfigStatus.className = "token-status error"
            proxyConfigStatus.style.display = "block"
          }
          
          showToast("error", "Error", "Failed to save proxy configuration")
        })
      })
    }
  }

  // Toggle Proxy Configuration card
  const proxyConfigHeader = document.querySelectorAll(".card-header")[1]
  if (proxyConfigHeader) {
    const toggleBtn = proxyConfigHeader.querySelector(".toggle-btn")
    const proxyConfigContent = document.getElementById("proxyConfigContent")

    if (toggleBtn && proxyConfigContent) {
      toggleBtn.addEventListener("click", function () {
        const expanded = this.getAttribute("aria-expanded") === "true"
        this.setAttribute("aria-expanded", !expanded)

        if (expanded) {
          proxyConfigContent.classList.remove("expanded")
          // Wait for transition to complete before hiding
          setTimeout(() => {
            proxyConfigContent.style.display = "none"
          }, 300)
        } else {
          proxyConfigContent.style.display = "block"
          // Small delay to ensure display:block is applied first
          setTimeout(() => {
            proxyConfigContent.classList.add("expanded")
          }, 10)
        }
      })
    }
  }

  // Show Page
  function showPage(pageId) {
    pages.forEach((page) => (page.style.display = "none"))
    document.getElementById(`${pageId}-page`).style.display = "block"
    pageTitle.textContent = pageId.charAt(0).toUpperCase() + pageId.slice(1)

    navItems.forEach((item) => item.classList.remove("active"))
    document.querySelector(`[data-page="${pageId}"]`).classList.add("active")

    if (pageId === "dashboard") {
      updateStats()
      updateRecentScans()
    } else if (pageId === "reports") {
      loadReports()
    } else if (pageId === "projects") {
      loadProjects()
      setupProjectSearch()
    }

    // Close mobile sidebar after navigation
    if (window.innerWidth <= 768) {
      sidebar.classList.remove("active")
    }
  }

  // Initialize all token forms
  setupTokenForm("wpscan")
  setupTokenForm("dnsdumpster")
  setupTokenForm("mxtoolbox")
  setupTokenForm("apininja")
  setupTokenForm("intelx")
  
  // Initialize proxy configuration
  setupProxyConfiguration()

  // Initialization
  showPage("dashboard")
  updateStats()
  updateRecentScans()
})