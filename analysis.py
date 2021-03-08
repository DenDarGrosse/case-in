from xgboost import XGBClassifier as xgb
from models import PredictedFailure
from config import db
import numpy as np
import pandas as pd

modelFileName = 'model.model'


def load_model():
    model = xgb(n_jobs=-1)
    model.load_model(modelFileName)
    return model


def save_model(model):
    model.save_model(modelFileName)


def predict(machine, first_date, last_date):

    model = load_model()
    telemetry = pd.read_sql(
        "SELECT * FROM telemetry where machineID={machine} AND datetime between '{first_date}' AND '{last_date}'"
        .format(machine=machine, first_date=first_date, last_date=last_date), con=db.engine.connect())

    errors = pd.read_sql(
        "SELECT * FROM errors where machineID={machine} AND datetime between '{first_date}' AND '{last_date}'"
        .format(machine=machine, first_date=first_date, last_date=last_date), con=db.engine.connect())

    maint = pd.read_sql(
        "SELECT * FROM maints where machineID={machine} AND datetime between '{first_date}' AND '{last_date}'"
        .format(machine=machine, first_date=first_date, last_date=last_date), con=db.engine.connect())

    failures = pd.read_sql(
        "SELECT * FROM failures where machineID={machine} AND datetime between '{first_date}' AND '{last_date}'"
        .format(machine=machine, first_date=first_date, last_date=last_date), con=db.engine.connect())

    machines = pd.read_sql(
        "SELECT * FROM machines where machineID={machine}"
        .format(machine=machine, first_date=first_date, last_date=last_date), con=db.engine.connect())

    errors["errorID"] = errors["errorID"].astype("category")
    maint["comp"] = maint["comp"].astype("category")
    machines["model"] = machines["model"].astype("category")
    failures["failure"] = failures["failure"].astype("category")

    fields = ["volt", "rotate", "pressure", "vibration"]

    temp = [
        pd.pivot_table(
            telemetry,
            index="datetime",
            columns="machineID",
            values=col).resample("3H", closed="left", label="right").mean().unstack()
        for col in fields
    ]

    telemetry_mean_3h = pd.concat(temp, axis=1)
    telemetry_mean_3h.columns = [col + "mean_3h" for col in fields]
    telemetry_mean_3h.reset_index(inplace=True)

    temp = [
        pd.pivot_table(
            telemetry,
            index="datetime",
            columns="machineID",
            values=col).resample("3H", closed="left", label="right").std().unstack()
        for col in fields
    ]

    telemetry_sd_3h = pd.concat(temp, axis=1)
    telemetry_sd_3h.columns = [i + "sd_3h" for i in fields]
    telemetry_sd_3h.reset_index(inplace=True)

    fields = ["volt", "rotate", "pressure", "vibration"]

    temp = [
        pd.pivot_table(
            telemetry,
            index="datetime",
            columns="machineID",
            values=col).rolling(window=24).mean().resample("3H", closed="left", label="right").first().unstack()
        for col in fields
    ]
    telemetry_mean_24h = pd.concat(temp, axis=1)
    telemetry_mean_24h.columns = [i + "mean_24h" for i in fields]
    telemetry_mean_24h.reset_index(inplace=True)
    telemetry_mean_24h = telemetry_mean_24h.loc[-telemetry_mean_24h["voltmean_24h"].isnull()]

    fields = ["volt", "rotate", "pressure", "vibration"]

    temp = [
        pd.pivot_table(
            telemetry,
            index="datetime",
            columns="machineID",
            values=col).rolling(window=24).std().resample("3H", closed="left", label="right").first().unstack(level=-1)
        for col in fields
    ]

    telemetry_sd_24h = pd.concat(temp, axis=1)
    telemetry_sd_24h.columns = [i + "sd_24h" for i in fields]
    telemetry_sd_24h.reset_index(inplace=True)
    telemetry_sd_24h = telemetry_sd_24h.loc[-telemetry_sd_24h["voltsd_24h"].isnull()]

    telemetry_feat = pd.concat([
        telemetry_mean_3h,
        telemetry_sd_3h.iloc[:, 2:6],
        telemetry_mean_24h.iloc[:, 2:6],
        telemetry_sd_24h.iloc[:, 2:6]], axis=1).dropna()

    error_count = pd.get_dummies(errors)
    error_count.columns = ["datetime", "machineID", "error1", "error2", "error3", "error4", "error5"]
    error_count_grouped = error_count.groupby(["machineID", "datetime"]).sum().reset_index()

    error_count_filtered = telemetry[["datetime", "machineID"]].merge(
        error_count_grouped,
        on=["machineID", "datetime"],
        how="left"
    ).fillna(0.0)

    fields = [
        "error%d" % i
        for i in range(1, 6)
    ]

    temp = [
        pd.pivot_table(
            error_count_filtered,
            index="datetime",
            columns="machineID",
            values=col).rolling(window=24).sum().resample("3H", closed="left", label="right").first().unstack()
        for col in fields
    ]

    error_count_total = pd.concat(temp, axis=1)
    error_count_total.columns = [i + "count" for i in fields]
    error_count_total.reset_index(inplace=True)
    error_count_total = error_count_total.dropna()

    comp_rep = pd.get_dummies(maint)
    comp_rep.columns = ["datetime", "machineID", "comp1", "comp2", "comp3", "comp4"]

    comp_rep = comp_rep.groupby(["machineID", "datetime"]).sum().reset_index()

    comp_rep = telemetry[["datetime", "machineID"]].merge(
        comp_rep,
        on=["datetime", "machineID"],
        how="outer").fillna(0).sort_values(by=["machineID", "datetime"]
                                           )

    components = ["comp1", "comp2", "comp3", "comp4"]
    for comp in components:
        comp_rep.loc[comp_rep[comp] < 1, comp] = None
        comp_rep.loc[-comp_rep[comp].isnull(), comp] = comp_rep.loc[-comp_rep[comp].isnull(), "datetime"]
        comp_rep[comp] = pd.to_datetime(comp_rep[comp].fillna(method="ffill"))

    comp_rep = comp_rep.loc[comp_rep["datetime"] > pd.to_datetime("2015-01-01")]

    for comp in components:
        comp_rep[comp] = (comp_rep["datetime"] - pd.to_datetime(comp_rep[comp])) / np.timedelta64(1, "D")

    final_feat = telemetry_feat.merge(error_count_total, on=["datetime", "machineID"], how="left")
    final_feat = final_feat.merge(comp_rep, on=["datetime", "machineID"], how="left")
    final_feat = final_feat.merge(machines, on=["machineID"], how="left")

    labeled_features = final_feat.merge(failures, on=["datetime", "machineID"], how="left")
    labeled_features["failure"] = labeled_features["failure"].astype(object).fillna(method="bfill", limit=7)
    labeled_features["failure"] = labeled_features["failure"].fillna("none")
    labeled_features["failure"] = labeled_features["failure"].astype("category")

    model_dummies = pd.get_dummies(labeled_features["model"])
    labeled_features = pd.concat([labeled_features, model_dummies], axis=1)
    labeled_features.drop("model", axis=1, inplace=True)

    predicted_failure = model.predict(labeled_features)
    return predicted_failure

"""    telemetry = telemetry.drop('date', axis=1)
    telemetry = telemetry.astype('float')
    telemetry = telemetry.astype({'id_machine': 'int32'})

    predicted_failure = model.predict(df)"""
    #predicted_failure = predicted_failure.loc[predicted_failure[]]
