############################################################
#This file trains the data with the logistic regression
#analysis and returns the ranked element.
############################################################

#myArgs <- c("outputToR.tsv","dermovate.ne3.massimo.tagged", "estracombi.ne3.massimo.tagged")
myArgs <- commandArgs(trailingOnly = TRUE)
for (i in 2:length(myArgs)) {
  if(i == 2) {
    f = scan(file = myArgs[i], what = "char", sep = "\n", quiet = T)  
  }else{
    f = c(f, scan(file = myArgs[i], what = "char", sep = "\n", quiet =T))
  }
}

g <- unlist(strsplit(paste(f, sep = "", collapse = ""), split = "</unit>"))

############################################################
#(1)antecedent relation
############################################################
x <- gsub("<unit [^\\>]*?>.*?</unit>","",paste(f, sep = "", collapse = ""), perl = T)
y=gsub("^.*?<ante ","",unlist(strsplit(x, split = "</anchor>")), perl = T)

current = c()
rel = c()
antecedent = c()
for(i in 1:length(y)){
  temp = gsub("^current=\'([^\']*?)\' rel=\'([^\']*?)\'><anchor antecedent=\'([^\']*?)\'> ","\\1\t\\2\t\\3",y[i], perl =T)
  temp = unlist(strsplit(temp, split = "\t"))
  current[i] <- temp[1]
  rel[i] <- temp[2]
  antecedent[i] <- temp[3]
}

ante.relation <- data.frame(current, antecedent, rel)
ante.relation$current <- as.character(ante.relation$current)
ante.relation$antecedent <- as.character(ante.relation$antecedent)
############################################################
#(2) Create a matrix
############################################################
g1 <- gsub("^.*<unit[^>]*?>","",g)
g1 <- g1[grep("<ne ",g1)]


#2-1 nextCB: the Cb entity of the next sentence
r = matrix(0, ncol = 22)
colnames(r) <- c( "sentID", "id", "cat", "per", "num", "gen", "gf","deix","lftype","onto","ani","count", "generic","structure","reference", "loeb", "den", "disc","cb","pnform", "nextCB", "HighestCf")
for( i in 1:length(g1)){
  #for each sentence
  temp = unlist(strsplit(g1[i], split = "<ne "))
  temp <- temp[grep("^id", temp)]
  temp <- gsub(">.*$", "",temp, perl = T)
  for(j in 1:length(temp)) {
    features <- unlist(strsplit(temp[j], split = " "))
    if(i!=1 || j!=1) r <- rbind(r, rep(0,22))
    r[nrow(r), 1] <- i
    for(k in 1:length(features))  r[nrow(r), gsub("=.*$","",features[k], perl = T)] <- gsub("^.*?=\'([^\']*?)\'","\\1",features[k], perl = T)
    if ("cb=\'cb-yes\'" %in% features) {
      nextCB <- gsub("id=\'([^\']*?)\'","\\1",perl = T, features[grep("id=", features)])
      r[grep(paste("^",i-1,"$", sep = "", collapse = ""), r[,"sentID"]), "nextCB"] <- nextCB
    }
  }
}
r <- data.frame(r, stringsAsFactors = F)
r$id <- as.character(r$id)
r$HighestCf <- as.character(r$HighestCf)

########
#(3)Mark whether it is the salient highest-ranked element
#(a) Just bewteen the adjacent pairs
#(b) Next Cb
#######

#nrow(r)
for(i in 1:nrow(r)){ 
  search.word <- r$nextCB[i]
  if(length(grep(paste("^",search.word,"$", sep ="", collapse =""), ante.relation[,"current"]))!=0){
    r$HighestCf[i]<-ifelse(
      r$id[i] %in% ante.relation[grep(paste("^",search.word,"$", sep ="", collapse =""), ante.relation[,"current"]),"antecedent"]
      , yes = "1"
      , no = "0"
    )
  }
}

#r$nextCB[16:20]


############################################################
#(4) Feature Selection
############################################################
#Renaming for the xrenner form
#givenness: This corresponds to the "infstat" in xrenner
r[r$disc == "disc-old",]$disc <- "giv"
r[r$disc == "disc-new",]$disc <- "new"
r[r$disc == "0",]$disc <- "new"
r[r$disc == "no-disc",]$disc <- "new"
#unique(r$disc);head(r$disc)

#(a) Transform: pronoun
r$pronoun <- 0
if("pn" %in% r$cat) r[r$cat=="pn",]$pronoun <- 1

#(b) Transform: givenness: This corresponds to the "infstat" in xrenner

#(c) Transform: gen (because this does not have male or female)
#r[r$gen == "fem",]$gen <- "female"
#r[r$gen == "masc",]$gen <- "male"
#unique(r$gen);head(r$gen)

levels(r$gen) <- c("neut", "undersp-gen", "male", "female")

#(d) Transform gf features
r$subj <-0
r[r$gf == "subj", ]$subj <-1

r$obj <-0
r[r$gf == "obj", ]$obj <-1



#Manually, I selected the following features
#fs<-c("sentID","id","cat","gen","gf","onto","ani","reference","loeb","disc","cb","pnform","nextCB","HighestCf")
fs<-c("sentID","id","onto","disc","pronoun","nextCB","HighestCf", "subj", "obj")
r1 <- r[,fs]

r1$HighestCf <- as.numeric(r1$HighestCf)
glm1 <- glm(HighestCf~ . , data = r1[,! colnames(r1) %in% c("sentID","id", "nextCB")], family = "binomial")

############################################################
#(5) From pythont to R
############################################################
myArgs <- commandArgs(trailingOnly = TRUE)
data <- read.csv(file = myArgs[1], header = FALSE, sep = ",", stringsAsFactors = F)
colnames(data) <- c("text", "sentID", "pr", "onto","V4", "disc", "gf")
data$pr <- gsub("\\s+","", data$pr, perl = T)




############################################################
#(6) Transform features
############################################################
#6-1 gender
data$gen <- "undersq-gen"
if("male" %in% data$V4) data[data$V4=="male",]$gen <- "male"
if("female" %in% data$V4) data[data$V4=="female",]$gen <- "female"

#6-2 pronoun
data$pronoun <- 0
if("pronoun" %in% data$pr) data[data$pr=="pronoun",]$pronoun <- 1

#6-3 GF
data$subj <- 0
data$obj <- 0
if(length(grep(".*subj", data$gf, perl = T))>0) data[grep(".*subj", data$gf, perl = T),]$subj <- 1
if(length(grep(".*obj", data$gf, perl = T))>0) data[grep(".*obj", data$gf, perl = T),]$obj <- 1

############################################################
#(7) Predict the probability
############################################################
data$predict.prob <- 0
for(i in 1:nrow(data)) data$predict.prob[i] <- predict(glm1, data[i,])

############################################################
#(8) Ranking
#If there is a tie, they are ordered based on the linearity.
############################################################
data$Rank <- 0
for(i in 1:length(unique(data$sentID))) {
  idx <- grep(paste("^",i,"$", collapse  = "", sep = ""), data$sentID, perl = T)
  for(j in 1:length(idx)) data$Rank[idx[j]] <- order(data[idx,]$predict.prob, decreasing = T)[j]
}

############################################################
#(9) Return to the STDOUT
############################################################
#This should be written in the STDOUT
cat(paste(data$text, "\t", data$Rank, "\n", collapse = "", sep = ""))

