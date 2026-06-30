"""
JalDrishti ML Model Trainer
Trains XGBoost classifiers for ADD, Cholera, and Typhoid prediction
Uses temporal split and SMOTE for class imbalance
"""

import pandas as pd
import numpy as np
import joblib
import os
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import roc_auc_score, precision_score, recall_score, f1_score, classification_report
from xgboost import XGBClassifier
from imblearn.over_sampling import SMOTE

print("=" * 70)
print("JalDrishti ML Model Trainer")
print("=" * 70)

# Load feature matrix
print("\n📊 Loading feature matrix...")
try:
    df = pd.read_csv('data/processed/final_feature_matrix.csv')
    print(f"  ✓ Loaded {len(df):,} rows")
except FileNotFoundError:
    print("  ❌ final_feature_matrix.csv not found")
    print("  Run: python src/feature_engineering.py")
    exit(1)

# Define feature columns (exclude metadata and targets)
exclude_cols = ['district_code', 'district_name', 'state_name', 'year', 'month', 
                'add_outbreak', 'cholera_outbreak', 'typhoid_outbreak']
feature_cols = [col for col in df.columns if col not in exclude_cols]

print(f"\n📋 Feature columns: {len(feature_cols)}")
for i, col in enumerate(feature_cols[:10], 1):
    print(f"  {i:2d}. {col}")
if len(feature_cols) > 10:
    print(f"  ... and {len(feature_cols) - 10} more")

# Temporal split: train on 2019-2021, validate on 2022, test on 2023
print("\n⏱ Creating temporal train/val/test split...")
train_df = df[df['year'].isin([2019, 2020, 2021])]
val_df = df[df['year'] == 2022]
test_df = df[df['year'] == 2023]

print(f"  Train (2019-2021): {len(train_df):,} rows")
print(f"  Val (2022): {len(val_df):,} rows")
print(f"  Test (2023): {len(test_df):,} rows")

# Create models directory
os.makedirs('models', exist_ok=True)

# Train models for each disease
diseases = ['add', 'cholera', 'typhoid']
results = []

for disease in diseases:
    print("\n" + "=" * 70)
    print(f"Training {disease.upper()} Model")
    print("=" * 70)
    
    target_col = f'{disease}_outbreak'
    
    # Prepare data
    X_train = train_df[feature_cols].values
    y_train = train_df[target_col].values
    
    X_val = val_df[feature_cols].values
    y_val = val_df[target_col].values
    
    X_test = test_df[feature_cols].values
    y_test = test_df[target_col].values
    
    print(f"\n📊 Class distribution:")
    print(f"  Train: {y_train.sum()} positive / {len(y_train)} total ({y_train.mean()*100:.1f}%)")
    print(f"  Val: {y_val.sum()} positive / {len(y_val)} total ({y_val.mean()*100:.1f}%)")
    print(f"  Test: {y_test.sum()} positive / {len(y_test)} total ({y_test.mean()*100:.1f}%)")
    
    # Apply SMOTE for class imbalance
    print(f"\n⚖️ Applying SMOTE for class balance...")
    
    # Calculate safe k_neighbors
    n_minority = int(y_train.sum())
    k_neighbors = min(5, max(1, n_minority - 1))
    
    print(f"  Minority class samples: {n_minority}")
    print(f"  Using k_neighbors: {k_neighbors}")
    
    if n_minority > 1:
        smote = SMOTE(random_state=42, k_neighbors=k_neighbors)
        X_train_balanced, y_train_balanced = smote.fit_resample(X_train, y_train)
        
        print(f"  After SMOTE: {len(X_train_balanced):,} samples")
        print(f"  Positive class: {y_train_balanced.sum()} ({y_train_balanced.mean()*100:.1f}%)")
    else:
        print(f"  ⚠️ Insufficient minority samples for SMOTE, using original data")
        X_train_balanced = X_train
        y_train_balanced = y_train
    
    # Calculate scale_pos_weight
    scale_pos_weight = (len(y_train_balanced) - y_train_balanced.sum()) / y_train_balanced.sum() if y_train_balanced.sum() > 0 else 1
    
    print(f"\n🔧 Training XGBoost with GridSearchCV...")
    
    # Base model
    base_model = XGBClassifier(
        n_estimators=200,
        scale_pos_weight=scale_pos_weight,
        use_label_encoder=False,
        eval_metric='logloss',
        random_state=42,
        n_jobs=-1
    )
    
    # Grid search parameters
    param_grid = {
        'max_depth': [4, 6, 8],
        'learning_rate': [0.05, 0.1]
    }
    
    grid_search = GridSearchCV(
        base_model,
        param_grid,
        cv=3,
        scoring='roc_auc',
        n_jobs=-1,
        verbose=1
    )
    
    grid_search.fit(X_train_balanced, y_train_balanced)
    
    print(f"\n✓ Best parameters: {grid_search.best_params_}")
    print(f"  Best CV score: {grid_search.best_score_:.4f}")
    
    # Get best model
    model = grid_search.best_estimator_
    
    # Evaluate on validation set
    print(f"\n📊 Validation Set Performance:")
    y_val_pred = model.predict(X_val)
    y_val_proba = model.predict_proba(X_val)[:, 1]
    
    val_auc = roc_auc_score(y_val, y_val_proba) if len(np.unique(y_val)) > 1 else 0.0
    val_precision = precision_score(y_val, y_val_pred, zero_division=0)
    val_recall = recall_score(y_val, y_val_pred, zero_division=0)
    val_f1 = f1_score(y_val, y_val_pred, zero_division=0)
    
    print(f"  ROC-AUC: {val_auc:.4f}")
    print(f"  Precision: {val_precision:.4f}")
    print(f"  Recall: {val_recall:.4f}")
    print(f"  F1-Score: {val_f1:.4f}")
    
    # Evaluate on test set
    print(f"\n📊 Test Set Performance:")
    y_test_pred = model.predict(X_test)
    y_test_proba = model.predict_proba(X_test)[:, 1]
    
    test_auc = roc_auc_score(y_test, y_test_proba) if len(np.unique(y_test)) > 1 else 0.0
    test_precision = precision_score(y_test, y_test_pred, zero_division=0)
    test_recall = recall_score(y_test, y_test_pred, zero_division=0)
    test_f1 = f1_score(y_test, y_test_pred, zero_division=0)
    
    print(f"  ROC-AUC: {test_auc:.4f}")
    print(f"  Precision: {test_precision:.4f}")
    print(f"  Recall: {test_recall:.4f}")
    print(f"  F1-Score: {test_f1:.4f}")
    
    # Save results
    results.append({
        'Disease': disease.upper(),
        'Val_AUC': val_auc,
        'Val_Precision': val_precision,
        'Val_Recall': val_recall,
        'Val_F1': val_f1,
        'Test_AUC': test_auc,
        'Test_Precision': test_precision,
        'Test_Recall': test_recall,
        'Test_F1': test_f1
    })
    
    # Save model
    model_path = f'models/trained_model_{disease}.pkl'
    joblib.dump(model, model_path)
    print(f"\n💾 Saved model → {model_path}")
    
    # Create and save SHAP explainer (mock for now)
    print(f"  Creating SHAP explainer...")
    try:
        import shap
        explainer = shap.TreeExplainer(model)
        shap_path = f'models/shap_explainer_{disease}.pkl'
        joblib.dump(explainer, shap_path)
        print(f"  ✓ Saved SHAP explainer → {shap_path}")
    except ImportError:
        print(f"  ⚠️ SHAP not available, skipping explainer save")

# Print summary table
print("\n" + "=" * 70)
print("MODEL PERFORMANCE SUMMARY")
print("=" * 70)

results_df = pd.DataFrame(results)
print("\nValidation Set (2022):")
print(results_df[['Disease', 'Val_AUC', 'Val_Precision', 'Val_Recall', 'Val_F1']].to_string(index=False))

print("\nTest Set (2023):")
print(results_df[['Disease', 'Test_AUC', 'Test_Precision', 'Test_Recall', 'Test_F1']].to_string(index=False))

print("\n" + "=" * 70)
print("✅ MODEL TRAINING COMPLETE")
print("=" * 70)
print(f"\n💾 Saved {len(diseases)} models to models/")
print(f"\n🚀 NEXT STEPS:")
print(f"  Run: streamlit run dashboard/app.py")
print("=" * 70)
