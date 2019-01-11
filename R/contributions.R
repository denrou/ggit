#' Contributions
#'
#' Get some statistics about working projects
#'
#' @inheritParams list_git
#' @inheritParams git2r::contributions
#'
#' @export
#'
contributions <- function(path = Sys.getenv("HOME"), breaks = "day", by = "author", progress = "interactive") {
  lst_git <- list_git(path = path)
  pb <- progress_bar$new(progress, length(lst_git))
  contributions <- purrr::safely(function(path) {
    pb$tick()
    git2r::contributions(repo = path, breaks = breaks, by = by) %>%
      dplyr::mutate(path = path)
  })
  res <- purrr::map(list_git(path = path), contributions)
  pb$close()
  tibble::as_tibble(suppressWarnings(purrr::compact(purrr::map_dfr(res, "result")))) %>%
    dplyr::group_by_at(c("when", "author")) %>%
    dplyr::summarise_at("n", sum) %>%
    dplyr::ungroup()
}
