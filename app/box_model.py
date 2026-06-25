"""
Ocean Box Model Wrapper with Full Observability
Includes: Structured logging, Performance tracking, Error handling
"""

import os
import time
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

try:
    from def_solar_BATS import (
        surface_clear_sky_solar_v1,
        two_layered_model_stocks_interaction_change_light,
        two_layered_model_concen_interaction_change_light
    )
except ImportError:
    raise ImportError("def_solar_BATS.py not found!")

from statsmodels.tsa.seasonal import MSTL
from scipy.stats import linregress
from sklearn.linear_model import LinearRegression
from app.logging_config import logger

_THIS_FILE_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_THIS_FILE_DIR)
OUTPUT_DIR = os.path.join(_PROJECT_ROOT, "outputs")
DATA_DIR = os.path.join(_PROJECT_ROOT, "data")
os.makedirs(OUTPUT_DIR, exist_ok=True)

COLORS = {
    "surface_chla": "#009E73",
    "subsurface_chla": "#56B4E9",
    "surface_p": "#D55E00",
    "subsurface_p": "#CC79A7",
    "surface_z": "#8B0000",
    "subsurface_z": "#0072B2",
    "surface_n": "#F0E442",
    "subsurface_n": "#999999",
    "trend_line": "black",
    "fit_line": "red"
}

STATION_CONFIG = {
    "BATS": {
        "latitude": 31,
        "models": ["BCC-CSM2-MAR", "CESM2-WACCM", "CMCC-CM2-SR5", "CMCC-ESM2", "GFDL-ESM4"],
        "parameter_file": "parameter_input_final.csv",
        "scenarios": ["ssp126", "ssp245", "ssp585"],
        "file_pattern": "{variable}_Omon_{model}_{scenario}_r1i1p1f1_1990-2100_BATS_daily.csv"
    },
    "HOT": {
        "latitude": 22,
        "models": ["CanESM5", "CESM2-WACCM", "CMCC-CM2-SR5", "CMCC-ESM2",
                   "EC-Earth-Veg", "EC-Earth3", "GFDL-ESM4", "IPSL-CM6A-LR", "NorESM2-MM"],
        "parameter_file": "parameter_input_final_HOT.csv",
        "scenarios": ["ssp126", "ssp245", "ssp585"],
        "file_pattern": "{variable}_Omon_{model}_{scenario}_r1i1p1f1_1990-2100_HOT_daily.csv"
    }
}


def load_parameters(station: str) -> np.ndarray:
    """Load parameters with timing"""
    start = time.time()
    
    if station not in STATION_CONFIG:
        raise ValueError(f"Unknown station: {station}")
    
    config = STATION_CONFIG[station]
    param_file = os.path.join(DATA_DIR, station, "parameters", config["parameter_file"])
    
    if not os.path.exists(param_file):
        raise FileNotFoundError(f"Parameter file not found: {param_file}")
    
    df = pd.read_csv(param_file)
    duration = time.time() - start
    
    logger.info("parameters_loaded")
    
    return df['default']


def load_cmip6_data(station: str, model: str, scenario: str, variable: str) -> np.ndarray:
    """Load CMIP6 data with timing"""
    start = time.time()
    
    if station not in STATION_CONFIG:
        raise ValueError(f"Unknown station: {station}")
    
    config = STATION_CONFIG[station]
    file_pattern = config["file_pattern"]
    filename = file_pattern.format(variable=variable, model=model, scenario=scenario)
    filepath = os.path.join(DATA_DIR, station, model, scenario, filename)
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Data file not found: {filepath}")
    
    df = pd.read_csv(filepath)
    data = df[variable].values if variable in df.columns else df.iloc[:, 0].values
    
    duration = time.time() - start
    
    logger.info("cmip6_data_loaded")
    
    return data


def extract_trend_and_fit(monthly_data, var_name, skip_months=300):
    """Extract trend with error handling"""
    try:
        decomposition = MSTL(monthly_data, periods=12)
        decomposition = decomposition.fit()
        trend = decomposition.trend
    except Exception as e:
        logger.warning("mstl_decomposition_failed")
        trend = monthly_data
    
    if len(trend) <= skip_months:
        return trend, None, None, None, None
    
    fit_start_idx = skip_months
    n_fit_points = len(trend) - fit_start_idx
    decimal_years = np.arange(n_fit_points)
    y_fit = trend[fit_start_idx:]
    
    try:
        model = LinearRegression()
        model.fit(decimal_years.reshape(-1, 1), y_fit)
        fit_line = model.predict(decimal_years.reshape(-1, 1))
        
        slope, intercept, r_value, p_value, std_err = linregress(decimal_years, y_fit)
        slope_per_year = slope * 12
        
        logger.info("trend_fitting_completed")
        
        return trend, fit_line, slope_per_year, p_value, fit_start_idx
    except Exception as e:
        logger.error("trend_fitting_failed")
        return trend, None, None, None, None


def generate_trend_plots(monthly_df, output_prefix, station, model, scenario):
    """Generate trend plots with timing"""
    start = time.time()
    
    logger.info("trend_plot_generation_started")
    
    stats_results = []
    
    fig, axes = plt.subplots(4, 2, figsize=(16, 14))
    fig.suptitle(f'Trend Analysis (4×2) - {station}/{model}/{scenario}', fontsize=16)
    
    variables_config = [
        ("Chla", "Chla", "Chla_sub", "mg m$^{-2}$", "mg m^-2/yr"),
        ("Pstr", "Pstr", "Pstr_sub", "mmolN m$^{-2}$", "mmolN m^-2/yr"),
        ("Zstr", "Zstr", "Zstr_sub", "mmolN m$^{-2}$", "mmolN m^-2/yr"),
        ("Nutstr", "Nutstr", "Nd_str", "mmolN m$^{-2}$", "mmolN m^-2/yr")
    ]
    
    for row_idx, (display_name, surface_col, subsurface_col, y_label, unit) in enumerate(variables_config):
        # Surface
        ax_surf = axes[row_idx, 0]
        trend_s, fit_s, slope_s, p_s, skip_s = extract_trend_and_fit(
            monthly_df[surface_col].values, f"{display_name}_surface"
        )
        if trend_s is not None:
            ax_surf.plot(monthly_df['Date'], trend_s, linewidth=1.5, color=COLORS["surface_chla"], label='Trend')
            if fit_s is not None and skip_s is not None:
                ax_surf.plot(monthly_df['Date'].iloc[skip_s:], fit_s, "--", linewidth=2,
                            color=COLORS["fit_line"],
                            label=f'Fit (slope={slope_s:.4f}/yr, p={p_s:.4f})')
                stats_results.append({
                    "Variable": display_name,
                    "Layer": "Surface",
                    "Slope": round(slope_s, 6),
                    "P_value": round(p_s, 6),
                    "Unit": unit
                })
        ax_surf.set_ylabel(y_label, fontsize=10)
        ax_surf.set_title(f'{display_name} - Surface', fontsize=11, fontweight='bold')
        ax_surf.legend(fontsize=8)
        ax_surf.grid(True, alpha=0.3)
        
        # Subsurface
        ax_sub = axes[row_idx, 1]
        trend_d, fit_d, slope_d, p_d, skip_d = extract_trend_and_fit(
            monthly_df[subsurface_col].values, f"{display_name}_subsurface"
        )
        if trend_d is not None:
            ax_sub.plot(monthly_df['Date'], trend_d, linewidth=1.5, color=COLORS["subsurface_chla"], label='Trend')
            if fit_d is not None and skip_d is not None:
                ax_sub.plot(monthly_df['Date'].iloc[skip_d:], fit_d, "--", linewidth=2,
                           color=COLORS["fit_line"],
                           label=f'Fit (slope={slope_d:.4f}/yr, p={p_d:.4f})')
                stats_results.append({
                    "Variable": display_name,
                    "Layer": "Subsurface",
                    "Slope": round(slope_d, 6),
                    "P_value": round(p_d, 6),
                    "Unit": unit
                })
        ax_sub.set_ylabel(y_label, fontsize=10)
        ax_sub.set_title(f'{display_name} - Subsurface', fontsize=11, fontweight='bold')
        ax_sub.legend(fontsize=8)
        ax_sub.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plot_path = os.path.join(OUTPUT_DIR, f"{output_prefix}_trends.png")
    fig.savefig(plot_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    
    # Summary CSV
    summary_data = []
    for display_name, var_key in [("Chla", "Chla"), ("Pstr", "Pstr"), ("Zstr", "Zstr"), ("Nutstr", "Nd_str")]:
        surface_data = next((item for item in stats_results if item["Variable"] == var_key and item["Layer"] == "Surface"), None)
        subsurface_data = next((item for item in stats_results if item["Variable"] == var_key and item["Layer"] == "Subsurface"), None)
        
        if surface_data:
            surface_str = f"{surface_data['Slope']:.6f} / {surface_data['P_value']:.6f}"
        else:
            surface_str = "N/A"
        
        if subsurface_data:
            subsurface_str = f"{subsurface_data['Slope']:.6f} / {subsurface_data['P_value']:.6f}"
        else:
            subsurface_str = "N/A"
        
        units_dict = {
            "Chla": "mg m^-2/yr",
            "Pstr": "mmolN m^-2/yr",
            "Zstr": "mmolN m^-2/yr",
            "Nutstr": "mmolN m^-2/yr"
        }
        
        summary_data.append({
            "Variable": display_name,
            "Surface (Slope / P-value)": surface_str,
            "Subsurface (Slope / P-value)": subsurface_str,
            "Unit": units_dict.get(display_name, "")
        })
    
    summary_df = pd.DataFrame(summary_data)
    summary_csv_path = os.path.join(OUTPUT_DIR, f"{output_prefix}_trends_summary.csv")
    summary_df.to_csv(summary_csv_path, index=False)
    
    duration = time.time() - start
    
    logger.info("trend_plot_generation_completed")
    
    return plot_path, summary_csv_path


def run_box_model(
    station: str,
    model: str,
    scenario: str,
    start_year: int,
    end_year: int,
    output_type: str,
    run_id: str
) -> dict:
    """Run model with full observability"""
    
    total_start = time.time()
    
    if station not in STATION_CONFIG:
        logger.error("invalid_station")
        raise ValueError(f"Unknown station: {station}")
    
    logger.info("model_run_started")
    
    try:
        # Load parameters
        logger.info("loading_parameters")
        param_start = time.time()
        parame = load_parameters(station)
        param_time = time.time() - param_start
        
        config = STATION_CONFIG[station]
        Lat = config["latitude"]
        year = np.arange(start_year, end_year + 1, 1)
        
        # Extract all parameters
        SolarK = parame[0]
        AtmAtt_fix = parame[2]
        Kdw = parame[1]
        Kdp = parame[4]
        ParFrac = parame[3]
        Ks = parame[5]
        Nd = parame[6]
        Nut = parame[7]
        Mprev = parame[8]
        alpha = parame[9]
        Vmax = parame[10]
        P = parame[11]
        m = parame[12]
        Gamma = parame[13]
        Z = parame[14]
        CN = parame[15]
        a = parame[16]
        k_e = parame[17]
        mum = parame[18]
        mup = parame[19]
        mug = parame[20]
        muz = parame[21]
        alpha_sub = parame[22]
        Vmax_sub = parame[23]
        a_sub = parame[24]
        k_e_sub = parame[25]
        Gamma_sub = parame[26]
        m_sub = parame[27]
        CN_sub = parame[28]
        P_sub = parame[29]
        Z_sub = parame[30]
        Kdp_sub = parame[31]
        Chla = parame[32]
        Chla_sub = parame[33]
        M_EU = parame[34]
        thetam = parame[35]
        X_sub = parame[36]
        
        # Load data
        logger.info("loading_cmip6_data")
        data_start = time.time()
        rsdscs_values = load_cmip6_data(station, model, scenario, "rsdscs")
        rsds_values = load_cmip6_data(station, model, scenario, "rsds")
        mld_data = load_cmip6_data(station, model, scenario, "mlotst")
        data_time = time.time() - data_start
        
        mld_filled = mld_data
        
        para1 = (Lat, year, SolarK, AtmAtt_fix)
        I_clearsky = surface_clear_sky_solar_v1(para1)
        AtmAtt_dy = rsdscs_values / I_clearsky
        frac_cs = rsds_values / rsdscs_values
        
        para_sub = (alpha_sub, Kdp_sub, Vmax_sub, a_sub, k_e_sub, Gamma_sub, m_sub, CN_sub, X_sub)
        initial_conditions2 = (P, Nut, Z, Mprev, mld_filled, P_sub, Z_sub, M_EU, Chla, Chla_sub)
        parameters_surface = (SolarK, ParFrac, Kdw, Kdp, Vmax, alpha, Ks, Nd, m, Gamma, CN, mum, mup, mug, muz, a, k_e, thetam)
        
        # Run model
        logger.info("model_calculation_started")
        model_start = time.time()
        
        if output_type.lower() == "concentration":
            logger.info("using_concentration_model")
            Pstr, Nutstr, Zstr, I, I_sub, Nd_str, Pstr_sub, Zstr_sub, Depth_EU, Chla_str, Chla_sub_str, X_ratio = \
                two_layered_model_concen_interaction_change_light(
                    Lat, year, initial_conditions2, parameters_surface, para_sub, AtmAtt_dy, frac_cs
                )
        else:
            logger.info("using_integration_model")
            Pstr, Nutstr, Zstr, I, I_sub, Nd_str, Pstr_sub, Zstr_sub, Depth_EU, Chla_str, Chla_sub_str, X_ratio = \
                two_layered_model_stocks_interaction_change_light(
                    Lat, year, initial_conditions2, parameters_surface, para_sub, AtmAtt_dy, frac_cs
                )
        
        model_time = time.time() - model_start
        
        logger.info("model_calculation_completed")
        
        # Create output dataframe
        date_range = pd.date_range(start=f"{start_year}-01-01", periods=len(Pstr), freq='D')
        output_df = pd.DataFrame({
            'Date': date_range,
            'Depth_EU': Depth_EU,
            'MLZ': mld_filled,
            'I_sub': I_sub,
            'I': I,
            'Pstr': Pstr,
            'Pstr_sub': Pstr_sub,
            'Chla': Chla_str,
            'Chla_sub': Chla_sub_str,
            'Zstr': Zstr,
            'Zstr_sub': Zstr_sub,
            'Nutstr': Nutstr,
            'Nd_str': Nd_str,
        })
        
        csv_path = os.path.join(OUTPUT_DIR, f"{run_id}_output.csv")
        output_df.to_csv(csv_path, index=False)
        
        logger.info("output_csv_saved")
        
        # Generate plots
        logger.info("generating_plots")
        plot_start = time.time()
        
        output_df.set_index('Date', inplace=True)
        monthly_median_df = output_df.resample('ME').median()
        monthly_median_df = monthly_median_df.reset_index()
        
        fig, axes = plt.subplots(3, 1, figsize=(12, 10))
        
        axes[0].plot(monthly_median_df['Date'], monthly_median_df['Pstr'], linewidth=2, color='green', label='Surface')
        axes[0].plot(monthly_median_df['Date'], monthly_median_df['Pstr_sub'], linewidth=2, color='blue', label='Subsurface')
        axes[0].set_ylabel('Phytoplankton [mmolN m$^{-2}$]')
        axes[0].set_title(f'{station} - {model} - {scenario}')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)
        
        axes[1].plot(monthly_median_df['Date'], monthly_median_df['Chla'], linewidth=2, color='green', label='Surface')
        axes[1].plot(monthly_median_df['Date'], monthly_median_df['Chla_sub'], linewidth=2, color='blue', label='Subsurface')
        axes[1].set_ylabel('Chlorophyll [mg m$^{-2}$]')
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)
        
        axes[2].plot(monthly_median_df['Date'], monthly_median_df['MLZ'], linewidth=2, color='red')
        axes[2].set_ylabel('Mixed Layer Depth [m]')
        axes[2].set_xlabel('Year')
        axes[2].grid(True, alpha=0.3)
        
        plot_path = os.path.join(OUTPUT_DIR, f"{run_id}.png")
        fig.savefig(plot_path, dpi=120, bbox_inches='tight')
        plt.close(fig)
        
        # Trend plots
        trend_plot_path, summary_csv_path = generate_trend_plots(monthly_median_df, run_id, station, model, scenario)
        
        plot_time = time.time() - plot_start
        
        logger.info("plots_generated")
        
        # Final statistics
        total_time = time.time() - total_start
        mean_pstr = round(float(np.nanmean(Pstr)), 3)
        mean_pstr_sub = round(float(np.nanmean(Pstr_sub)), 3)
        mean_chla = round(float(np.nanmean(Chla_str)), 3)
        mean_mlz = round(float(np.nanmean(mld_filled)), 3)
        
        logger.info("model_run_completed")
        
        return {
            "station": station,
            "model": model,
            "scenario": scenario,
            "output_type": output_type,
            "start_year": start_year,
            "end_year": end_year,
            "latitude": Lat,
            "mean_surface_phytoplankton": mean_pstr,
            "mean_subsurface_phytoplankton": mean_pstr_sub,
            "mean_chlorophyll": mean_chla,
            "mean_mld": mean_mlz,
            "plot_path": plot_path,
            "trend_plot_path": trend_plot_path,
            "trend_summary_csv": summary_csv_path,
            "data_path": csv_path,
            "performance_metrics": {
                "total_time_seconds": round(total_time, 2),
                "parameter_load_time": round(param_time, 2),
                "data_load_time": round(data_time, 2),
                "model_run_time": round(model_time, 2),
                "plotting_time": round(plot_time, 2)
            },
            "status": "success"
        }
        
    except Exception as e:
        logger.error("model_run_failed")
        raise
