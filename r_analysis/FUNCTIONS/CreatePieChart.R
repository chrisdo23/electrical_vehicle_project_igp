

CreatePieChart <- function(data,
                           colX,
                           colY) {
  
  colX <- ensym(colX)
  colY <- ensym(colY)
  
  chart <- data %>%
    hchart(
      "pie", hcaes(x = !!colX, y = !!colY),
      name = quo_name(colY)
    ) %>% 
    FormatTooltip()
  
  return(chart)
  
  
}