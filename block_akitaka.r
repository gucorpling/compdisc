#--------------------------------------------------
#Section 0: libraries
#--------------------------------------------------
library("qdapDictionaries")
#--------------------------------------------------
#Section 1: Stop words
#--------------------------------------------------
stop.words <- function.words;length(stop.words)
#--------------------------------------------------
#Section 2: Define the function
#--------------------------------------------------
source("blocking.r")
#--------------------------------------------------
#Section 3: Set the working directory
#--------------------------------------------------
setwd("C:/Users/owner/OneDrive/Documents/44_25 LING 765 Discourse Modeling/data")
files = dir(pattern = "^GUM.*txt")
#--------------------------------------------------
#Section 4: run the codes
#--------------------------------------------------
#[Parameters]
#(a) halfwindowSize: k (the 1/2 of the window size)
#(b)smoothing: 2 blocks
#--------------------------------------------------
#4.1: parameter setting
#--------------------------------------------------
halfWindowSize = 2
smoothing = 2
#--------------------------------------------------
#4.2: Results
#--------------------------------------------------
results <- list()#for the sentence id
for (i in 1:4){
  r <- blocking(halfWindowSize, files[i], encoding = "UTF-8",smoothing = smoothing , plot = F
                , main = gsub("^GUM_voyage_([^_]*?)_noheads.txt","\\1",files[i]))
  results[[i]] <- r$topic.shift
}
results
