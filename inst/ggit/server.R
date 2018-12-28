server <- function(input, output, session) {
    tbl_repo <- eventReactive(
        eventExpr = input$button_path,
        valueExpr = {
            path <- if (input$text_path == "") Sys.getenv("HOME") else input$text_path
            req(file.exists(path))
            tbl_git(path = path)
        },
        ignoreNULL = FALSE)

    fetched_repo <- eventReactive(input$button_fetch, fetch_all(progress = "shiny"))
    fetched_prune_repo <- eventReactive(input$button_fetch_prune, fetch_all(progress = "shiny", prune = TRUE))

    output$box_repo <- renderValueBox({
        req(tbl_repo)
        n <- length(unique(tbl_repo()$repo))
        valueBox(n, "repositories", icon = icon("git"))
    })

    output$box_branches_not_pushed <- renderValueBox({
        req(tbl_repo)
        n <- sum(is.na(tbl_repo()$remote))
        valueBox(n, "branches not sync", icon = icon("chalkboard"), color = "orange")
    })

    output$box_fetched_error <- renderValueBox({
        req(fetched_repo)
        n <- length(compact(map(fetched_repo(), "error")))
        valueBox(n, "Broken origin", icon = icon("unlink"), color = "red")
    })

    output$gt_repo <- render_gt({
        req(tbl_repo)
        tbl_repo() %>%
            gather(flag, branch, local, remote) %>%
            filter(!is.na(branch)) %>%
            group_by(repo, branch) %>%
            summarise(
                last_fetch  = as.character(unique(last_fetch)),
                last_commit = round(as.numeric(now() - unique(last_commit), units = "days")),
                code        = ("remote" %in% flag) + 2 * ("local" %in% flag),
            ) %>%
            arrange(basename(repo), desc(code)) %>%
            mutate(new_repo = c(first(repo), rep(NA_character_, n() - 1))) %>%
            mutate_at(vars(starts_with("last_")), function(x) c(first(x), rep(NA, length(x) - 1))) %>%
            ungroup() %>%
            mutate(repo = if_else(is.na(new_repo), NA_character_, basename(new_repo))) %>%
            gt() %>%
            tab_style(
                style = cells_styles(text_style = "italic", text_weight = "bold"),
                locations = cells_data(columns = vars(branch), rows = code == 3)
            ) %>%
            tab_style(
                style = cells_styles(text_style = "italic", text_decorate = "underline"),
                locations = cells_data(columns = vars(branch), rows = code == 2)
            ) %>%
            tab_style(
                style = cells_styles(text_color = "LightGray"),
                locations = cells_data(columns = vars(branch), rows = code == 1)
            ) %>%
            cols_hide(vars(code, new_repo)) %>%
            fmt_datetime(vars(last_fetch)) %>%
            fmt_missing(vars(repo), missing_text = "") %>%
            fmt_missing(starts_with("last_")) %>%
            gt::cols_label(repo = "Repository", branch = "Branch", last_fetch = "Date Last Fetch", last_commit = "Days Since Last Commit")

    })
}
