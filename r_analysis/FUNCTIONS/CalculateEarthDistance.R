#'Calculate Earth Distance
#'@description Calculate spherical distance from Long-Lat using distHaversine function
#'@param data: a dataframe containing columns of origin and destination Longitude - Latitude
#'@param colOriginLong: column name of origin Longitude
#'@param colOriginLat: column name of origin Latitude
#'@param colDestinationLong: column name of destination Longitude
#'@param colDestinationLat: column name of destination Latitude
#'
#'@return A dataframe of the input dataframe with added column Distance is the distance in km from origin to destination points.
#'@examples
#'output <- CalculateEarthDistance(data = origin_dest_data,
#'colOriginLong = OriginLongitude, colOriginLat = OriginLatitude,
#'colDestinationLong = DestinationLongitude, colDestinationLat = DestinationLatitude)


CalculateEarthDistance <- function(data,
                                   colOriginLong,
                                   colOriginLat,
                                   colDestinationLong,
                                   colDestinationLat) {

  require(geosphere)

  colOriginLong <- enquo(colOriginLong)
  colOriginLat <- enquo(colOriginLat)
  colDestinationLong <- enquo(colDestinationLong)
  colDestinationLat <- enquo(colDestinationLat)

  data_output <- data %>%
    mutate(Distance = distHaversine(cbind(!!colOriginLong, !!colOriginLat),
                                    cbind(!!colDestinationLong, !!colDestinationLat))/1000)

  return(data_output)

}
