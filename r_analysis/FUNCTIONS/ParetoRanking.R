ParetoRanking <- function(.data, value) {
  value <- enquo(value)
  Dataset <- .data %>%
    mutate(value = ifelse(is.na(!!value), 0, !!value),
           percentage = value/sum(value)) %>%
    arrange(desc(percentage)) %>%
    mutate(cummulative_percentage = cumsum(percentage))
  return(Dataset)
}
