83.9% accuracy. Zero churners identified.

That is what an all-“no churn” prediction achieves on the test set in my first Retail Wireless Data Science Lab project.

It makes a useful starting question: what should a churn model actually be judged on?

For Week 1, I compared regularized logistic regression and gradient boosting using 3,150 observed telecom records from UCI’s Iranian Churn dataset.

The first important result came before modelling: 300 repeated rows. I kept identical predictor profiles together across every split, then nested preprocessing, tuning and probability calibration inside development folds. The final 639-row test set stayed outside model selection.

Three findings stood out:

• Ranking improved. Gradient boosting reached 0.930 average precision versus 0.772 for logistic regression. The boosting estimate’s conditional 95% profile-bootstrap interval was 0.881–0.966.

• Calibration was not an automatic improvement. Sigmoid calibration slightly worsened Brier error: 0.0361 before versus 0.0372 after. Lower is better. The prespecified calibrated model stayed the primary result rather than being replaced after seeing the test scores.

• Capacity made the result tangible. The top 64 predictions contained 63 of the 103 churn labels: 61.2% captured while reviewing roughly 10% of records.

That last number is useful for discussing prioritization. It is not evidence that a retention offer would prevent those customers from leaving.

My main takeaway: ranking, probability quality and business impact are three different questions. A strong answer to the first does not settle the other two.

The carousel walks through the baseline, model comparison, calibration result, review queue and feature-availability check.

This is a personal public-data learning project, using a historical Iranian sample—not employer data or evidence of current U.S. carrier performance.

Next week: forecasting telecom complaint volumes from real dated records, with rolling backtests and uncertainty intervals.

Code, results and reproducible charts:
https://github.com/Himalytics/wireless-data-science/tree/main/projects/01_churn_risk

#DataScience #MachineLearning #Telecom #AppliedML
