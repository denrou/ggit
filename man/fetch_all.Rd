% Generated by roxygen2: do not edit by hand
% Please edit documentation in R/fetch_all.R
\name{fetch_all}
\alias{fetch_all}
\title{Fetch All Repositories}
\usage{
fetch_all(path = Sys.getenv("HOME"), progress = "interactive",
  prune = FALSE)
}
\arguments{
\item{path}{a character vector of full path names; the default corresponds to the `HOME` directory. This parameter is then passed in [list.dirs]}

\item{progress}{either "interactive" or "shiny" or NULL. Indicate what backend should be used to print a progress bar.
The "interactive" choice uses the `dplyr` backend (see [`dplyr::progress_estimated`](dplyr::progress_estimated)).
The "shiny" choice uses the `shiny` backend (see [`shiny::Progress`](shiny::Progress)).
The NULL choice does not print any progress bar.}

\item{prune}{should `fetch --prune` be called.}
}
\description{
Find all repositories from a path which have a remote defined and fetch all of them.
}
