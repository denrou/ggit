
<!-- README.md is generated from README.Rmd. Please edit that file -->

# ggit

The goal of ggit is to help manage multiple `git` repositories. It first
list all available repositories by scanning all files recursively from a
starting path. Then, some actions can be performed such as:

  - Fetching all repositories in one command
  - Listing all repositories with a broken remote
  - Print the date of the last pull

## Installation

You can install the current version of ggit with:

``` r
remotes::install_github("denrou/ggit")
```

## Example

List all repositories located in the HOME directory

``` r
ggit::tbl_git(path = Sys.getenv("HOME"))
#> # A tibble: 174 x 6
#>    repo      local remote last_fetch          last_commit         n_authors
#>    <chr>     <chr> <chr>  <dttm>              <dttm>                  <int>
#>  1 /home/dr… mast… master 2018-12-28 11:35:03 2018-02-20 12:11:41        54
#>  2 /home/dr… <NA>  relea… 2018-12-28 11:35:03 2018-02-20 12:11:41        54
#>  3 /home/dr… <NA>  relea… 2018-12-28 11:35:03 2018-02-20 12:11:41        54
#>  4 /home/dr… <NA>  relea… 2018-12-28 11:35:03 2018-02-20 12:11:41        54
#>  5 /home/dr… <NA>  relea… 2018-12-28 11:35:03 2018-02-20 12:11:41        54
#>  6 /home/dr… mast… <NA>   NA                  2018-12-26 12:26:37         1
#>  7 /home/dr… mast… master 2018-12-28 11:35:08 2017-01-27 20:19:21         1
#>  8 /home/dr… mast… master 2018-12-28 11:35:08 2014-01-10 12:06:49         1
#>  9 /home/dr… mast… master 2018-12-28 10:22:47 2013-06-07 14:04:33         3
#> 10 /home/dr… mast… <NA>   NA                  2016-06-24 23:35:53         1
#> # ... with 164 more rows
```

## Shiny application

A shiny application is included within the package
([`shiny`](https://github.com/rstudio/shiny) must be installed). Just
use:

``` r
ggit::run_app()
```

Here is a screenshot of the application:

![Alt
text](inst/images/Screenshot_2018-12-28%20Glance%20Git%20Repositories.png?raw=true
"Screenshot ggit shiny application")
