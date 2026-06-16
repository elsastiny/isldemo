import pandas as pd
import numpy as np
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import joblib

def augment_handed_data(data: pd.DataFrame) -> pd.DataFrame:
    augmented_rows = []
    for _, row in data.iterrows():
        mirrored = row.copy()
        for i in range(21):
            mirrored[f"x{i}"] = 1.0 - row[f"x{i}"]
        if row["hand"] == "Left":
            mirrored["hand"] = "Right"
        elif row["hand"] == "Right":
            mirrored["hand"] = "Left"
        augmented_rows.append(mirrored)
    return pd.DataFrame(augmented_rows)

# Load dataset
data = pd.read_csv("gesture_data.csv")

print(data.head())

print("\nGesture Counts:")
print(data["gesture"].value_counts())

print("\nTotal Samples:")
print(len(data))

if len(data) < 30:
    print("WARNING: Dataset is small. Collect more samples for better accuracy.")

augmented = augment_handed_data(data)
data = pd.concat([data, augmented], ignore_index=True)
print("\nTotal Samples after augmentation:")
print(len(data))

# Features
X = pd.get_dummies(data.drop("gesture", axis=1), columns=["hand"])

# Labels
y = data["gesture"]

cv = StratifiedKFold(n_splits=min(4, len(y)), shuffle=True, random_state=42)
model = RandomForestClassifier(
    n_estimators=300,
    max_depth=12,
    min_samples_leaf=2,
    class_weight="balanced_subsample",
    random_state=42,
    n_jobs=-1
)

cv_scores = cross_val_score(model, X, y, cv=cv, scoring="accuracy")
print(f"Cross-validation accuracy: {cv_scores.mean():.2f} (+/- {cv_scores.std():.2f})")

model.fit(X, y)

y_pred = model.predict(X)
accuracy = accuracy_score(y, y_pred)
print(f"Training accuracy: {accuracy * 100:.2f}%")
print("\nClassification report:")
print(classification_report(y, y_pred))

# Save model
joblib.dump(model, "gesture_model.pkl")

print("Model saved as gesture_model.pkl")