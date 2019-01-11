
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
#> # A tibble: 177 x 6
#>    repo      local remote last_fetch          last_commit         n_authors
#>    <chr>     <chr> <chr>  <dttm>              <dttm>                  <int>
#>  1 /home/dr… mast… master 2018-12-28 11:35:03 2018-02-20 12:11:41        54
#>  2 /home/dr… <NA>  relea… 2018-12-28 11:35:03 2018-02-20 12:11:41        54
#>  3 /home/dr… <NA>  relea… 2018-12-28 11:35:03 2018-02-20 12:11:41        54
#>  4 /home/dr… <NA>  relea… 2018-12-28 11:35:03 2018-02-20 12:11:41        54
#>  5 /home/dr… <NA>  relea… 2018-12-28 11:35:03 2018-02-20 12:11:41        54
#>  6 /home/dr… mast… <NA>   NA                  2019-01-04 15:15:36         1
#>  7 /home/dr… mast… master 2018-12-28 11:35:08 2017-01-27 20:19:21         1
#>  8 /home/dr… mast… master 2018-12-28 11:35:08 2014-01-10 12:06:49         1
#>  9 /home/dr… mast… master 2018-12-28 10:22:47 2013-06-07 14:04:33         3
#> 10 /home/dr… mast… <NA>   NA                  2016-06-24 23:35:53         1
#> # … with 167 more rows
```

Get all contributions for all projects

``` r
ggit::contributions()
#> # A tibble: 3,262 x 3
#>    when       author                                      n
#>    <date>     <chr>                                   <int>
#>  1 2002-05-17 dj@dcde13d4-9b1b-0410-ac9e-ef07de68c835     5
#>  2 2002-05-18 dj@dcde13d4-9b1b-0410-ac9e-ef07de68c835     8
#>  3 2002-05-20 dj@dcde13d4-9b1b-0410-ac9e-ef07de68c835     3
#>  4 2002-06-25 dj@dcde13d4-9b1b-0410-ac9e-ef07de68c835     3
#>  5 2002-08-24 dj@dcde13d4-9b1b-0410-ac9e-ef07de68c835     1
#>  6 2002-09-10 dj@dcde13d4-9b1b-0410-ac9e-ef07de68c835     7
#>  7 2002-12-18 dj@dcde13d4-9b1b-0410-ac9e-ef07de68c835     2
#>  8 2003-05-16 dj@dcde13d4-9b1b-0410-ac9e-ef07de68c835     2
#>  9 2003-11-04 dj@dcde13d4-9b1b-0410-ac9e-ef07de68c835     1
#> 10 2003-12-01 dj@dcde13d4-9b1b-0410-ac9e-ef07de68c835     4
#> # … with 3,252 more rows
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
