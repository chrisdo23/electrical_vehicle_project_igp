

CreateLineChart <- function(data
                            , colY
                            , colX
                            , colYTitle
                            , showAverageValue = TRUE) {

  colX <- ensym(colX)
  colY <- ensym(colY)

  avg_value <- data %>%
    group_by(!!colX) %>%
    summarise(!!colY := sum(!!colY)) %>%
    ungroup()

  avg_value <- mean(avg_value %>% select(!!colY) %>% unlist())

  chart <- data %>%
    hchart(
      'line', hcaes(x = !!colX, y = !!colY)
    ) %>%
    hc_yAxis(title = list(text = colYTitle), min = 0,
             plotLines = list(list(label = list(text = str_c("Average: ", round(avg_value))),
                                   color = "#041f33",
                                   width = 2,
                                   value = avg_value,
                                   dashStyle = "dash",
                                   zIndex = 15))) %>%
    hc_colors(colors = CreateTikiNgonColor()) %>%
    FormatTooltip(valueDecimal = 0) %>%
    ExportingAndZoomHighcharter()

  if(showAverageValue == FALSE) {

    chart <- data %>%
      hchart(
        'line', hcaes(x = !!colX, y = !!colY),
      ) %>%
      hc_yAxis(title = list(text = colYTitle), min = 0) %>%
      hc_colors(colors = CreateTikiNgonColor()) %>%
      FormatTooltip(valueDecimal = 0) %>%
      ExportingAndZoomHighcharter()
  }


  return(chart)



}
