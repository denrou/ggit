#' Configurations
#'
#' Get a data frame of the different git configurations
#'
#' @inheritParams list_git
#'
#' @export
#'
configs <- function(path = Sys.getenv("HOME"), progress = "interactive") {
  lst_git <- list_git(path = path)
  pb <- progress_bar$new(progress, length(lst_git))
  configs <- purrr::safely(function(path) {
    pb$tick()
    get_config(path) %>%
      dplyr::mutate(path = path)
  })
  res <- purrr::map(list_git(path = path), configs)
  pb$close()
  tibble::as_tibble(suppressWarnings(purrr::compact(purrr::map_dfr(res, "result"))))
}

get_config <- function(path) {
  repo <- git2r::repository(path = path)
  config_all <- git2r::config(repo = repo)
  dplyr::as_tibble(merge_nested_lists(config_all[["global"]], config_all[["local"]]))
}
