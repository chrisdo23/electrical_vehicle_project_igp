


CreatePolygonMap <- function(mapData,
                             regionCol,
                             valueCol,
                             valueName,
                             binScale,
                             colorVector,
                             centralPoint = c(115.8473879, -2.415299)) {
  
  require(leaflet)
  valueCol <- enquo(valueCol)
  regionCol <- enquo(regionCol)
  
  valueColName <- quo_name(valueCol)
  regionColName <- quo_name(regionCol)
  palette_value <- ColorScale(colorVec = colorVector,
                                 bins = binScale,
                                 value = mapData[[valueColName]])
  
  javascript <- sprintf("function(btn, mapData){ mapData.setView([%f, %f], 5); }",
                        centralPoint[2],
                        centralPoint[1])
  
  # Layer groups, popup definition
  group_value <- valueName
  
  popupContent <- paste(sep = "<br/>",
                        str_c("<b>", mapData[[regionColName]], "</b>"),
                        str_c(valueName, ": ",
                              format(mapData[[valueColName]],
                                     big.mark = ",",
                                     digits = 2,
                                     scientific = FALSE)))
  
  map <- rlang::eval_tidy(rlang::quo_squash(quo({
    leaflet(mapData) %>%
      # Draw Open Street Map layer
      # addTiles("https://tiles.stadiamaps.com/tiles/alidade_smooth/{z}/{x}/{y}{r}.png") %>%
      addProviderTiles(providers$CartoDB.Positron
                       ,  options = providerTileOptions(minZoom=10, maxZoom=18)) %>%
      # Draw value layer
      addPolygons(color = "black",
                  weight = 1,
                  fillColor = ~palette_value(!!valueCol),
                  fillOpacity = 0.6,
                  group = group_value,
                  label = ~paste0("<b>", !!regionCol, "</b>",
                                  " : ",
                                  format(!!valueCol, digits = 2, big.mark = ",")) %>% lapply(HTML),
                  labelOptions = labelOptions(noHide = F, direction = "auto",
                                              textsize = "10px"),
                  popup = popupContent) %>%
      # Add home button
      addEasyButton(easyButton(icon = "fa-globe",
                               title = "Home",
                               onClick = JS(javascript))) %>%
      # Add legend
      addLegend(position = "bottomright",
                pal = palette_value,
                values = ~!!valueCol,
                title = valueName,
                group = group_value,
                # labFormat = labelFormat(suffix = str_c(" ", "ton")),
                opacity = 1) #%>%
    # Add layer control
    # addLayersControl(
    #   baseGroups = c("Open Street Map"),
    #   overlayGroups = group_value,
    #   position = "topleft")
  } %>%
    setView(lng = centralPoint[1], lat = centralPoint[2], 5)
  )))
  
  return(map)
  
  
}
