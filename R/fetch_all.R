#' Fetch All Repositories
#'
#' Find all repositories from a path which have a remote defined and fetch all of them.
#'
#' @inheritParams tbl_git
#' @param progress either "interactive" or "shiny" or NULL. Indicate what backend should be used to print a progress bar.
#' The "interactive" choice uses the `dplyr` backend (see [`dplyr::progress_estimated`](dplyr::progress_estimated)).
#' The "shiny" choice uses the `shiny` backend (see [`shiny::Progress`](shiny::Progress)).
#' The NULL choice does not print any progress bar.
#' @param prune should `fetch --prune` be called.
#'
#' @export
#'
fetch_all <- function(path = Sys.getenv("HOME"), progress = "interactive", prune = FALSE) {
  df_git <- tbl_git(path = path)
  paths  <- unique(unlist(df_git[!is.na(df_git[["remote"]]), "repo"]))
  pb     <- progress_bar$new(progress, length(paths))
  res <- purrr::map2(paths, seq_along(paths), purrr::safely(function(path, i) {
    pb$tick(message = glue::glue("Fetching {basename(path)} ({i}/{length(paths)})"))
    print(path)
    if (prune) {
      warning(
        "As of version 0.23.0 of `git2r`, git_fetch_prune from libgit2 is not implemented yet.",
        "Using system call instead."
      )
      if (Sys.which("git")[1] == "") {
        stop("Can't find `git` call.")
      }
      system(glue::glue('cd "{path}"; git fetch --prune'))
    } else {
      suppressMessages(git2r::fetch(path, name = "origin"))
    }
  }))
  pb$close()
  invisible(res)
}
