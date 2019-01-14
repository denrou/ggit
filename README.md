
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
#> # A tibble: 178 x 6
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
#> # … with 168 more rows
```

Get all contributions for all projects

``` r
ggit::contributions()
#> # A tibble: 3,264 x 3
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
#> # … with 3,254 more rows
```

Get all configuration files for all projects:

``` r
ggit::configs()
#> # A tibble: 107 x 59
#>    core.hookspath gui.recentrepo user.email user.name user.signingkey
#>    <chr>          <chr>          <chr>      <chr>     <chr>          
#>  1 /home/drousse… /home/drousse… denis.rou… Denis Ro… 0AED04E390F0C3…
#>  2 /home/drousse… /home/drousse… deroussel… Denis Ro… 0AED04E390F0C3…
#>  3 /home/drousse… /home/drousse… denis.rou… Denis Ro… 0AED04E390F0C3…
#>  4 /home/drousse… /home/drousse… denis.rou… Denis Ro… 0AED04E390F0C3…
#>  5 /home/drousse… /home/drousse… denis.rou… Denis Ro… 0AED04E390F0C3…
#>  6 /home/drousse… /home/drousse… denis.rou… Denis Ro… 0AED04E390F0C3…
#>  7 /home/drousse… /home/drousse… denis.rou… Denis Ro… 0AED04E390F0C3…
#>  8 /home/drousse… /home/drousse… denis.rou… Denis Ro… 0AED04E390F0C3…
#>  9 /home/drousse… /home/drousse… denis.rou… Denis Ro… 0AED04E390F0C3…
#> 10 /home/drousse… /home/drousse… denis.rou… Denis Ro… 0AED04E390F0C3…
#> # … with 97 more rows, and 54 more variables: branch.master.merge <chr>,
#> #   branch.master.remote <chr>, core.bare <chr>, core.filemode <chr>,
#> #   core.logallrefupdates <chr>, core.repositoryformatversion <chr>,
#> #   remote.origin.fetch <chr>, remote.origin.url <chr>, path <chr>,
#> #   diff.gpg.binary <chr>, diff.gpg.textconv <chr>, push.default <chr>,
#> #   branch.dev.merge <chr>, branch.dev.remote <chr>,
#> #   `branch.sf-support.merge` <chr>, `branch.sf-support.remote` <chr>,
#> #   gitg.mainline <chr>, `branch.clean-EBImage.merge` <chr>,
#> #   `branch.clean-EBImage.remote` <chr>, branch.development.merge <chr>,
#> #   branch.development.remote <chr>, branch.issue100.merge <chr>,
#> #   branch.issue100.remote <chr>, remote.upstream.fetch <chr>,
#> #   remote.upstream.url <chr>, `branch.R-support.merge` <chr>,
#> #   `branch.R-support.remote` <chr>, branch.drone.merge <chr>,
#> #   branch.drone.remote <chr>, branch.yaml.merge <chr>,
#> #   branch.yaml.remote <chr>, branch.issue_2667.merge <chr>,
#> #   branch.issue_2667.remote <chr>, branch.ato.merge <chr>,
#> #   branch.ato.remote <chr>, branch.hid.merge <chr>,
#> #   branch.hid.remote <chr>, branch.demo.merge <chr>,
#> #   branch.demo.remote <chr>, `branch.site-meru.merge` <chr>,
#> #   `branch.site-meru.remote` <chr>, `branch.site-velizy.merge` <chr>,
#> #   `branch.site-velizy.remote` <chr>, branch.dro.merge <chr>,
#> #   branch.dro.remote <chr>, branch.issue1743.merge <chr>,
#> #   branch.issue1743.remote <chr>, commit.gpgsign <chr>,
#> #   gui.geometry <chr>, gui.wmstate <chr>,
#> #   `branch.issue#4319.merge` <chr>, `branch.issue#4319.remote` <chr>,
#> #   remote.master.fetch <chr>, remote.master.url <chr>
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
text](inst/images/Screenshot_2019-01-14%20Glance%20Git%20Repositories\(1\).png?raw=true
"Screenshot ggit shiny application") ![Alt
text](inst/images/Screenshot_2019-01-14%20Glance%20Git%20Repositories.png?raw=true
"Screenshot ggit shiny application")
