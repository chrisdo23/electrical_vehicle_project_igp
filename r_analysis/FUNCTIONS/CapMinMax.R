CapMinMax <- function(value, cap_type = "minmax" , val1 = 0, val2 = val1) {

  result <- value
  if(!is.numeric(value)) {return(value)}

  if ((toupper(cap_type) == "MINMAX") | (toupper(cap_type) == "MAXMIN")) {
    result <- ifelse(result > max(val1, val2), max(val1, val2), result)
    result <- ifelse(result < min(val1, val2), min(val1, val2), result)
    #print("minmax")
  } else if (toupper(cap_type) == "MIN") {
    result <- ifelse(result < min(val1, val2), min(val1, val2), result)
    #print("min")
  } else if (toupper(cap_type) == "MAX") {
    result <- ifelse(result > max(val1, val2), max(val1, val2), result)
    #print("max")
  }

  return(result)
}