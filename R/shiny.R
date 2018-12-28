#' Shiny application
#'
#' Run a shiny application to show git repository
#'
#' @export
#'
run_app <- function() {
  assert_shiny()
  shiny::runApp(system.file(package = "ggit", "ggit"))
}
