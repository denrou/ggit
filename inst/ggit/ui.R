header <- dashboardHeader(
    title = "Glance Git Repositories",
    titleWidth = 300
)

sidebar <- dashboardSidebar(
    width = 300,
    sidebarSearchForm("text_path", "button_path", label = "Directory to scan (default to HOME)", icon = icon("search")),
    div(
        id = "buttonmenu",
        actionButton("button_fetch", "Fetch all repositories", icon = icon("cloud-download-alt")),
        actionButton("button_fetch_prune", "Prune all repositories", icon = icon("eraser"))
    )
)

body <- dashboardBody(
    shiny::tags$head(shiny::tags$link(rel = "stylesheet", type = "text/css", href = "custom.css")),
    fluidPage(
        valueBoxOutput("box_repo"),
        valueBoxOutput("box_branches_not_pushed"),
        valueBoxOutput("box_fetched_error"),
        box(width = 12, gt_output("gt_repo"))
    )
)

dashboardPage(header, sidebar, body)
