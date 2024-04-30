Authorization <- function(EmailAddress = "*@tiki.vn", NewLogin = FALSE) {
  require(gargle)
  require(bigrquery)
  require(googlesheets4)
  require(googledrive)
  
  if (NewLogin) {
    gs4_auth()
    drive_auth()
    drive_user()
    bq_auth()
  } else {
    gs4_auth(email = EmailAddress)
    drive_auth(email = EmailAddress)
    drive_user()
    bq_auth(email = EmailAddress)
  }
}