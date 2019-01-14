header <- dashboardHeader(
    title = "Glance Git Repositories",
    titleWidth = 300
)

sidebar <- dashboardSidebar(
    width = 300,
    sidebarSearchForm("text_path", "button_path", label = "Directory to scan (default to HOME)", icon = icon("search")),
    sidebarMenu(
        menuItem(text = "Global", tabName = "global"),
        menuItem(text = "Statistics", menuSubItem("Plots", tabName = "statistics", ), uiOutput("input_select"), uiOutput("input_slider"))
    ),
    div(
        id = "buttonmenu",
        actionButton("button_fetch", "Fetch all repositories", icon = icon("cloud-download-alt")),
        actionButton("button_fetch_prune", "Prune all repositories", icon = icon("eraser"))
    )
)

body <- dashboardBody(
    shiny::tags$head(shiny::tags$link(rel = "stylesheet", type = "text/css", href = "custom.css")),
    tabItems(
        tabItem(
            tabName = "global",
            fluidPage(
                valueBoxOutput("box_repo"),
                valueBoxOutput("box_branches_not_pushed"),
                valueBoxOutput("box_fetched_error"),
                box(width = 12, gt_output("gt_repo"))
            )
        ),
        tabItem(
            tabName = "statistics",
            fluidPage(
                valueBoxOutput("box_total_commit"),
                valueBoxOutput("box_period_commit"),
                valueBoxOutput("box_mean_commit"),
                girafeOutput("girafe_commit")
            )
        )
    )

)

dashboardPage(header, sidebar, body)
