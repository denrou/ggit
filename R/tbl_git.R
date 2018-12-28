#' Build a Tibble of Git Repositories
#'
#' This function produces a tibble based on git repositories.
#'
#' @inheritParams list_git
#'
#' @importFrom magrittr %>%
#' @importFrom rlang .data
#'
#' @export
#'
tbl_git <- function(path = Sys.getenv("HOME")) {
  dirs <- list_git(path = path)
  purrr::map_df(dirs, function(dir) {
    repository  <- git2r::repository(dir)
    last_fetch  <- file.mtime(file.path(dir, ".git", "FETCH_HEAD")) # The file FETCH_HEAD is always updated with a fetch
    last_commit <- tryCatch(as.POSIXct(git2r::last_commit(repository)[["author"]][["when"]]), error = function(e) NA)
    n_authors   <- tryCatch(length(unique(git2r::contributions(repository, by = "author")[["author"]])), error = function(e) NA)
    local       <- git2r::branches(repository, flag = "local")
    remote      <- git2r::branches(repository, flag = "remote")
    tbl_local   <- tibble::tibble(repo = dir, local = names(local), flag = "local")
    tbl_remote  <- tibble::tibble(repo = dir, remote = names(remote), flag = "remote") %>%
      dplyr::mutate_at("remote", stringr::str_replace, pattern = "origin/", replacement = "") %>%
      dplyr::filter(!stringr::str_detect(remote, "HEAD"))
    dplyr::full_join(tbl_local, tbl_remote, by = c("repo", "local" = "remote")) %>%
      dplyr::mutate(remote      = dplyr::if_else(is.na(.data[["flag.y"]]), NA_character_, local),
                    local       = dplyr::if_else(is.na(.data[["flag.x"]]), NA_character_, local),
                    last_fetch  = last_fetch,
                    last_commit = last_commit,
                    n_authors   = n_authors) %>%
      dplyr::select(-c("flag.x", "flag.y"))
  })
}
