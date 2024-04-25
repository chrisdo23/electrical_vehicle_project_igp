FormalizeData <- function(data) {
  result <- data %>%
    mutate(across(matches(c("Sku", "SupplierId", "Order_Code", "Original_Order_Code", "Original_Code", "SellerId", "CustomerId")), as.character),
           across(matches(c("NetWeight", "Cogs", "SbdStockQuantity", "Nmv", "Cmv")), as.numeric)) %>%
    mutate_if(is.POSIXct, as_datetime) %>%
    mutate_if(is.POSIXlt, as_datetime) %>%
    mutate_if(is.POSIXt, as_datetime)
  return(result)
}
