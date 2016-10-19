blocking <- function(halfWindowSize
                     ,f
                     , encoding = ""
                     , plot = F
                     , smoothing = F
                     , NumOfBoundary=6
                     , main = ""
                     , stop.words=""
){
  if(stop.words=="")    library("qdapDictionaries"); stop.words <- function.words
  k = halfWindowSize
  #--------------------------------------------------
  #2-1: Load Sentences from each file
  #--------------------------------------------------
  sentences = scan(file = f, what = "char", sep = "\n", quiet = T,  encoding = encoding)
  #--------------------------------------------------
  #2-2: Frequency matrix
  #--------------------------------------------------
  #Def: mat (Matrix)
  #(a) for rows: words
  #(b) for columns: sentences
  words <- unique(tolower(unlist(strsplit(sentences, split = " "))))
  mat <- matrix(0, nrow = length(words), ncol = length(sentences));rownames(mat) <- words
  for (i in 1:length(sentences))  mat[tolower(unlist(strsplit(sentences[i], split = " "))),i] = 1
  
  #--------------------------------------------------
  #2-3: Removing the stopwords
  #--------------------------------------------------
  #Def: mat (Matrix)
  #(a) for rows: words but stopwords
  #(b) for columns: sentences
  #- - - - - - - - - - - - - - - - - - - - - - - - -   
  mat <- mat[!rownames(mat) %in% stop.words,]
  #--------------------------------------------------
  #2-4: Blocks
  #--------------------------------------------------
  #Def: block (Matrix)
  #(a) for rows: words but stopwords
  nrow = nrow(mat)
  #(b) for columns: number of blocks (= ncol)
  ncol = length(sentences) - (k-1) 
  #- - - - - - - - - - - - - - - - - - - - - - - - -   
  block <- matrix(0, nrow = nrow, ncol = ncol)
  rownames(block) <- rownames(mat)
  if(k == 1){
    for (i in 1:ncol) block[,i] <- mat[, i]
  }else{
    for (i in 1:ncol) block[,i] <- rowSums(mat[, i:(i+k-1)])
  }
  #--------------------------------------------------
  #2-5: Distance between blocks
  #--------------------------------------------------
  #[Aim] Distance are measured in terms of inner product
  #- - - - - - - - - - - - - - - - - - - - - - - - - 
  result <- vector("numeric", length = ncol-k)
  for (i in 1:(ncol-k)) result[i] = block[,i] %*% block[,i+k]
  
  #--------------------------------------------------
  #2-6: Smoothing
  #--------------------------------------------------
  #[Aim] if you specify the smoothing value, the results will get smoothed.
  #- - - - - - - - - - - - - - - - - - - - - - - - - 
  if(is.numeric(smoothing)) {
    for (i in (smoothing + 1):(length(result)-smoothing)) {
      result[i] = mean(result[(i-smoothing):(i+smoothing)])
    }
  }
  #--------------------------------------------------
  #2-7: Depth score
  #--------------------------------------------------
  #[Aim] the depth of the valley
  #- - - - - - - - - - - - - - - - - - - - - - - - - 
  depth.score <- vector("numeric", length = length(result))
  for (i in 2:(length(result)-1)) depth.score[i] <- (result[i-1] - result[i]) + (result[i+1] - result[i])
  
  #  for (i in 2:(length(result)-1)) {
  #    if((result[i-1] - result[i]) * (result[i+1] - result[i])<0) {
  #      depth.score[i] <- 0
  #    }
  #  }
  #order(depth.score, decreasing = T)[depth.score[order(depth.score, decreasing = T)]!=0]
  #--------------------------------------------------
  #2-8: Boundary Detection
  #--------------------------------------------------
  #[Aim] boundary is detected based on the septh.score
  #- - - - - - - - - - - - - - - - - - - - - - - - - 
  boundaries <- head(order(depth.score, decreasing = T), NumOfBoundary)
  
  topic.shift <- vector("numeric", length = length(sentences))
  topic.shift[1] <- 1 #the first sentence always initiates the boundary
  topic.shift[boundaries + k] <-1
  
  #--------------------------------------------------
  #2-9 Return
  #--------------------------------------------------
  return.value = list()
  return.value$topic.shift <- topic.shift
#  return.value$topic.shift <- as.logical(topic.shift)
  return.value$block <- block
  if(plot == T) return.value$plot = plot(x=((k+1):ncol), y=result, type = "l", main = main)
  return(return.value)
  #low.6 <- head(order(result, decreasing = F))
  #high.6 <- head(order(result, decreasing = T))
  #j=1
  #s_id <- low.6[j]; sentences[s_id:(s_id+k-1)]; sentences[(s_id+k):(s_id+2*k-1)]
  #s_id <- high.6[j]; sentences[s_id:(s_id+k-1)]; sentences[(s_id+k):(s_id+2*k-1)]
}

