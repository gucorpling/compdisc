Hi Amir,

Here is the RST relation labeler. the data comes from the rst_train.rsd on canvas.
The last five RST trees were separated into the test file. I did this because the rst_test.rsd
that was on canvas was missing true labels, as well as what was connected to what (RST dependency).

The labeler achieves an accuracy of about 30%. unfortunately every time I run it I get a different result.
I was getting a similar problem with my final paper. This makes me think that SKlearn's SVM is kinda broken.

I'm sad I only just realized this as it means some of the results from my final paper are potentially wrong.
Who knows maybe i did beat state of the art.

Anyway, I think the features i've used are pretty solid so if you want a stable result let me know, as all
i need to do is swap out the SVM.

James

