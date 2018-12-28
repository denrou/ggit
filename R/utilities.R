progress_bar <- R6::R6Class(
  "progress_bar",
  public = list(
    initialize = function(progress, n) {
      if (interactive() && progress == "interactive") {
        private$pb       <- dplyr::progress_estimated(n)
        private$progress <- "interactive"
      } else if (progress == "shiny") {
        assert_shiny()
        private$progress <- "shiny"
        private$pb       <- shiny::Progress$new(max = n)
      }
    },
    tick = function(...) {
      if (is.null(private$progress)) return(NULL)
      if (private$progress == "interactive") {
        private$pb$tick()$print()
      } else if (private$progress == "shiny") {
        private$pb$inc(amount = 1, ...)
      }
    },
    close = function() {
      if (is.null(private$progress)) return(NULL)
      if (private$progress == "interactive") {
        private$pb$stop()$print()
      } else if (private$progress == "shiny") {
        private$pb$close()
      }
    }
  ),
  private = list(pb = NULL, progress = NULL)
)

assert_shiny <- function() {
  if (!requireNamespace("shiny", quietly = TRUE)) {
    stop('Shiny must be installed to run this command. Use `install.package("shiny").`')
  }
}
