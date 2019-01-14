merge_nested_lists<- function(base, additional) {
  assertthat::assert_that(
    all(table(names(base)) == 1),
    all(table(names(additional)) == 1),
    msg = glue::glue("Names must be unique for both lists."))
  res       <- c(base, additional)
  counts    <- table(names(res))
  conflicts <- names(counts[counts > 1])
  for (conflict in conflicts) {
    ids <- which(names(res) == conflict)
    new_element <- if (is.list(base[[conflict]]) && is.list(additional[[conflict]])) {
      merge_nested_lists(base[[conflict]], additional[[conflict]])
    } else {
      new_element <- additional[[conflict]]
    }
    if (is.null(new_element)) {
      res[ids[1]] <- list(NULL)
    } else {
      res[[ids[1]]] <- new_element
    }
    res[ids[2]] <- NULL
  }
  res
}


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
  deps       <- desc::desc_get_deps(system.file("DESCRIPTION", package = "ggit"))
  shiny_deps <- unlist(deps[deps[["type"]] == "Suggests", "package"])
  if (!all(purrr::map_lgl(shiny_deps, requireNamespace, quietly = TRUE))) {
    stop('Some dependancies are missing to run the shiny application.',
         'Install them using `remotes::install_github("denrou/ggit")`')
  }
}
