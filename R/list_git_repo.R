#' List the Git Repository in a Directory/Folder
#'
#' This function produces a character vector of the names of directories where a `.git` folder can be found.
#'
#' @param path a character vector of full path names; the default corresponds to the `HOME` directory. This parameter is then passed in [list.dirs]
#'
#' @export
#'
list_git <- function(path = Sys.getenv("HOME")) {
  dirs <- list.files(
    path         = path,
    full.names   = TRUE,
    recursive    = TRUE,
    include.dirs = TRUE,
    pattern      = "^\\.git$",
    all.files    = TRUE
  )
  gsub("/.git$", "", dirs)
}
