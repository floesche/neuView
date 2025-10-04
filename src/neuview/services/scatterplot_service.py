"""
Interactive Scatterplot Service

Simplified service that coordinates other specialized services to create
interactive scatterplot page with plots related to the spatial metrics per type.
"""

import logging
from pathlib import Path
import pandas as pd

from ..result import Result, Ok, Err

from .index_service import IndexService
from .file_service import FileService

logger = logging.getLogger(__name__)

class ScatterplotService:
    """Service for creating scatterplots with markers for all available neuron types."""

    def __init__(self, config, page_generator):
        self.config = config
        self.page_generator = page_generator
        self._batch_neuron_cache = {}

        # Initialize cache manager for neuron type data
        self.cache_manager = None
        if config and hasattr(config, "output") and hasattr(config.output, "directory"):
            from ..cache import create_cache_manager
            self.cache_manager = create_cache_manager(config.output.directory)

    async def create_scatterplots(self, command) -> Result[str, str]:
            """Create a scatterplot containing markers for all neuron types found in the output directory."""
            try:
                logger.info("Starting plot creation using cached data")

                # Determine output directory
                output_dir = Path(command.output_directory or self.config.output.directory)
                if not output_dir.exists():
                    return Err(f"Output directory does not exist: {output_dir}")

                # Discover neuron types from cache or file scanning
                neuron_types, _ = IndexService.discover_neuron_types(self, output_dir)
                if not neuron_types:
                    return Err("No neuron type HTML files found in output directory")

                # Initialize connector if needed for database lookups
                connector = await IndexService.initialize_connector_if_needed(
                    self, neuron_types, output_dir
                )

                # Correct neuron names (convert filenames back to original names)
                corrected_neuron_types, _ = IndexService.correct_neuron_names(
                    self, neuron_types, connector
                )

                # Generate scatterplot data for corrected neuron types
                plot_data = self._generate_plot_data(corrected_neuron_types)
                print(plot_data)

                # Generate the plots

                # # Collect all generated file paths
                # generated_files = [str(output_dir / command.index_filename)]
                # if hasattr(self, "generated_files"):
                #     generated_files.extend(self.generated_files)

                return plot_data #Ok(generated_files)

            except Exception as e:
                logger.error(f"Failed to create optimized index: {e}")
                return Err(f"Failed to create index: {str(e)}")

    def _generate_plot_data(self, neuron_types):
        """Generate plot data from neuron types."""
        cached_data_lazy = (
            self.cache_manager.get_cached_data_lazy() if self.cache_manager else None
        )
        plot_data = []
        cached_count = 0
        missing_cache_count = 0

        for neuron_type, sides in neuron_types.items():
            # Check if we have cached data for this neuron type
            cache_data = cached_data_lazy.get(neuron_type) if cached_data_lazy else None

            entry = {
                "name": neuron_type,
                "total_count": 0,
                "left_count": 0,
                "right_count": 0,
                "middle_count": 0,
                "undefined_count": 0,
                "has_undefined": False,
                "spatial_metrics": {},
            }

            # Use cached data if available (NO DATABASE QUERIES!)
            if cache_data:
                entry["spatial_metrics"] = cache_data.spatial_metrics
                entry["total_count"] = cache_data.total_count
                entry["left_count"] = cache_data.soma_side_counts.get("left", 0)
                entry["right_count"] = cache_data.soma_side_counts.get("right", 0)
                entry["middle_count"] = cache_data.soma_side_counts.get("middle", 0)
                entry["undefined_count"] = cache_data.soma_side_counts.get("unknown", 0)
                entry["has_undefined"] = entry["undefined_count"] > 0
                
                logger.debug(f"Used cached data for {neuron_type}")
                cached_count += 1
            else:
                # No cached data available - use minimal defaults
                logger.debug(
                    f"No cached data available for {neuron_type}, using minimal defaults"
                )
                missing_cache_count += 1

            plot_data.append(entry)

        # Sort results
        plot_data.sort(key=lambda x: x["name"])

        if missing_cache_count > 0:
            logger.warning(
                f"Plot data generation completed: {len(plot_data)} entries, {cached_count} with cache, {missing_cache_count} missing cache. Run 'quickpage generate' to populate cache."
            )
        else:
            logger.info(
                f"Plot data generation completed: {len(plot_data)} entries, all with cached data"
            )
        return plot_data


    # # Make an svg - in JS when hover over - that marker is large. 
    # def _make_scatterplot(self, 
    #     xval:str
    # , yval:str
    # , roi_str:str
    # , style:dict
    # , sizing:dict
    # , plot_specs:dict
    # , star_neurons:list
    # , save_plot:bool=True) -> go.Figure:
    #     """
    #     Plot scatterplot with 'star_neuron' types highlighted.

    #     Parameters
    #     ----------
    #     xval : str
    #     Column of 'df' to be shown on the x-axis.
    #     yval : str
    #         Column of 'df' to be shown on the y-axis.
    #     roi_str : str
    #         Optic lobe region of interest to plot the data from.
    #     style : dict
    #         Dict containing the values of the fixed styling formatting variables.
    #     sizing : dict
    #         Dict containing the values of the size formatting variables.
    #     plot_specs : dict
    #         Dict containing the values of the formatting variables relevant to the specific plot.
    #     star_neurons : list
    #         List of 'star neurons' to highlight in the plot.
    #     save_plot : bool, default = True
    #         Whether to save the plot or only return it.

    #     Returns
    #     -------
    #     fig : go.Figure
    #         Formatted plotly scatterplot.
    #     """
    #     pio.kaleido.scope.mathjax = None

    #     assert plot_specs["colorscale"] in ["red", "group"]\
    #     , f"Colorscale must be 'red' or 'group', not '{plot_specs['colorscale']}'"

    #     # load the data
    #     df = load_and_process_df(roi_str=roi_str)
    #     if xval == "instance":
    #         df = df.sort_values(yval)

    #     df["markersize"] = float(sizing["markersize"])
    #     df["markerlinewidth"] = sizing["markerlinewidth"]
    #     df["text"] = ""

    #     if star_neurons:
    #         df.loc[df["instance"].isin(star_neurons), "markersize"] = (
    #             sizing["markersize"] * 1.75
    #         )
    #         df.loc[df["instance"].isin(star_neurons), "markerlinewidth"] = (
    #             sizing["markerlinewidth"] * 7
    #         )
    #         df.loc[df["instance"].isin(star_neurons), "group"] = 6

    #     # get sizing values
    #     if style["export_type"] == "svg":
    #         pixelsperinch = 72
    #     else:
    #         pixelsperinch = 96
    #     pixelspermm = pixelsperinch / 25.4
    #     plot_width = (sizing["fig_width"] - sizing["fig_margin"]) * pixelspermm
    #     plot_height = (sizing["fig_height"] - sizing["fig_margin"]) * pixelspermm
    #     fsize_ticks_px = sizing["fsize_ticks_pt"] * (1 / 72) * pixelsperinch
    #     fsize_title_px = sizing["fsize_title_pt"] * (1 / 72) * pixelsperinch

    #     cmap = Colormap("reds_5").to_plotly()  # colorscale == 'red'; default
    #     if plot_specs["colorscale"] == "group":
    #         cmap = [
    #             [0, "rgb(200, 200, 200)"]
    #         , [0.1666, "rgb(200, 200, 200)"]
    #         , [0.1666, "rgb(2, 158, 115)"]
    #         , [0.333, "rgb(2, 158, 115)"]
    #         , [0.333, "rgb(213, 94, 0)"]
    #         , [0.5, "rgb(213, 94, 0)"]
    #         , [0.5, "rgb(1,115,178)"]
    #         , [0.666, "rgb(1,115,178)"]
    #         , [0.6666, "rgb(222,143,5)"]
    #         , [0.833, "rgb(222,143,5)"]
    #         , [0.833, "rgb(204, 120, 188)"]
    #         , [1.0, "rgb(204, 120, 188)"]
    #         ]

    #     # set the maximum
    #     _, n_cols_region = find_neuropil_hex_coords(roi_str)

    #     fig = go.Figure()

    #     match yval:
    #         case "coverage_factor_trim":
    #             fig.add_shape(
    #                 type="line"
    #             , y0=1
    #             , x0=1
    #             , x1=n_cols_region
    #             , y1=1
    #             , layer="below"
    #             , line={"color": "grey", "width": 0.8, "dash": "solid"}
    #             )

    #         case "cell_size_cols":
    #             for multipl in [0.2, 0.5, 1, 2, 5]:
    #                 if multipl < 0.5 or multipl > 2:
    #                     line_width = 0.25
    #                 elif multipl != 1:
    #                     line_width = 0.4
    #                 else:
    #                     line_width = 0.8

    #                 fig.add_shape(
    #                     type="line"
    #                 , x0=1
    #                 , y0=n_cols_region * multipl
    #                 , x1=n_cols_region * multipl
    #                 , y1=1
    #                 , layer="below"
    #                 , line={"color": "grey", "width": line_width, "dash": "solid"}
    #                 )

    #     # add groups in order to ensure star neurons are plotted last
    #     gp_values = df["group"].sort_values(ascending=True).unique()
    #     for grp in gp_values:

    #         df_gp = df[df["group"] == grp]

    #         fig.add_trace(
    #             go.Scatter(
    #                 x=df_gp[xval]
    #             , y=df_gp[yval]
    #             , text=[df_gp["text"]]
    #             , textposition="top center"
    #             , customdata=np.stack(
    #                     (df_gp["instance"], df_gp[plot_specs["color_factor"]]), axis=-1
    #                 )
    #             , hovertemplate=plot_specs["hover_template"]
    #             , opacity=0.95
    #             , mode="markers"
    #             , marker={
    #                     "cmax": plot_specs["cmax"]
    #                 , "cmin": plot_specs["cmin"]
    #                 , "size": df_gp["markersize"]
    #                 , "color": df_gp[plot_specs["color_factor"]]
    #                 , "line": {
    #                         "width": df_gp["markerlinewidth"]
    #                     , "color": style["markerlinecolor"]
    #                     },
    #                     "colorscale": cmap,
    #                     "colorbar": {
    #                         "orientation": "v"
    #                     , "outlinecolor": style["linecolor"]
    #                     , "outlinewidth": sizing["axislinewidth"]
    #                     , "thickness": sizing["cbar_thickness"]
    #                     , "len": sizing["cbar_length"]
    #                     , "ticklen": sizing["cbar_tick_length"]
    #                     , "tickcolor": "black"
    #                     , "tickwidth": sizing["cbar_tick_width"]
    #                     , "tickmode": "array"
    #                     , "tickvals": plot_specs["tickvals"]
    #                     , "ticktext": plot_specs["ticktext"]
    #                     , "tickfont": {"size": fsize_ticks_px, "color": "black"}
    #                     , "title": {
    #                             "font": {
    #                                 "family": style["font_type"]
    #                             , "size": fsize_title_px
    #                             , "color": "black"
    #                             },
    #                             "side": "right"
    #                         , "text": plot_specs["cbar_title"]
    #                         }
    #                     }
    #                 }
    #             )
    #         )

    #     xlabel = get_axis_labels(xval, label_type="axis")
    #     ylabel = get_axis_labels(yval, label_type="axis")

    #     if plot_specs["log_x"]:
    #         typex = "log"
    #         tickformx = ".1r"
    #     else:
    #         typex = "-"
    #         tickformx = ""

    #     if plot_specs["log_y"]:
    #         typey = "log"
    #         tickformy = ".1r"
    #     else:
    #         typey = "-"
    #         tickformy = ""

    #     fig.update_layout(
    #         autosize=False,
    #         width=plot_width,
    #         height=plot_height,
    #         margin={
    #             "l": plot_width // 8,
    #             "r": 0,
    #             "b": plot_height // 4,
    #             "t": 0,
    #             "pad": plot_width // 30,
    #         },
    #         showlegend=False,
    #         paper_bgcolor="rgba(255,255,255,1)",
    #         plot_bgcolor="rgba(255,255,255,1)",
    #     )

    #     fig.update_xaxes(
    #         title={
    #             "font": {
    #                 "size": fsize_title_px,
    #                 "family": style["font_type"],
    #                 "color": style["linecolor"],
    #             },
    #             "text": xlabel,
    #         },
    #         title_standoff=(plot_height // 4) / 4,
    #         ticks="outside",
    #         ticklen=sizing["ticklen"],
    #         tickwidth=sizing["tickwidth"],
    #         tickfont={
    #             "family": style["font_type"],
    #             "size": fsize_ticks_px,
    #             "color": style["linecolor"],
    #         },
    #         tickformat=tickformx,
    #         tickcolor="black",
    #         type=typex,
    #         showgrid=False,
    #         showline=True,
    #         linewidth=sizing["axislinewidth"],
    #         linecolor=style["linecolor"],
    #         range=plot_specs["range_x"],
    #     )

    #     match xval:
    #         case "instance":
    #             fig.update_xaxes(title="", tickvals=[], visible=False)
    #         case "coverage_factor_trim":
    #             fig.update_xaxes(tickvals=[1, 2, 4, 8, 12])
    #         case "cell_size_cols":
    #             fig.update_xaxes(tickvals=[1, 10, 100, 1000])
    #         case "area_covered_pop":
    #             fig.update_xaxes(tickvals=[0, 200, 400, 600, 800, 1000])
    #         case "cols_covered_pop":
    #             fig.update_xaxes(tickvals=[0, 200, 400, 600, 800, 1000])
    #         case "population_size":
    #             fig.update_xaxes(tickvals=[1, 10, 100, 1000])

    #     fig.update_yaxes(
    #         title={
    #             "font": {
    #                 "size": fsize_title_px
    #             , "family": style["font_type"]
    #             , "color": style["linecolor"]
    #             }
    #         , "text": f"{ylabel}"
    #         }
    #     , title_standoff=(plot_width // 5) / 5
    #     , ticks="outside"
    #     , tickcolor="black"
    #     , ticklen=sizing["ticklen"]
    #     , tickwidth=sizing["tickwidth"]
    #     , tickfont={
    #             "size": fsize_ticks_px
    #         , "family": style["font_type"]
    #         , "color": "black"
    #         }
    #     , tickformat=tickformy
    #     , type=typey
    #     , showgrid=False
    #     , showline=True
    #     , linewidth=sizing["axislinewidth"]
    #     , linecolor=style["linecolor"]
    #     , scaleanchor="x"
    #     , scaleratio=1
    #     , anchor="free"
    #     , side="left"
    #     , overlaying="y"
    #     , range=plot_specs["range_y"]
    #     )

    #     match yval:
    #         case "coverage_factor_trim":
    #             fig.update_yaxes(tickvals=[1, 2, 4, 8, 12], scaleanchor=False)
    #         case "cell_size_cols":
    #             fig.update_yaxes(tickvals=[1, 10, 100, 1000])
    #         case "area_covered_pop":
    #             fig.update_yaxes(tickvals=[0, 200, 400, 600, 800, 1000])
    #         case "population_size":
    #             fig.update_yaxes(tickvals=[1, 10, 100, 1000])

    #     if save_plot:
    #         save_path = plot_specs["save_path"]
    #         assert isinstance(save_path, Path)\
    #         , f"save_path needs to be 'Path', not '{type(save_path)}'"
    #         save_path.mkdir(parents=True, exist_ok=True)

    #         basename = (
    #             save_path
    #             / f"{roi_str[:-3]}_{xval}_versus_{yval}_{sizing['fsize_title_pt']}pt_"
    #             f"w{sizing['fig_width']}_h{sizing['fig_height']}_cscale-{plot_specs['color_factor']}"
    #         )

    #         if style["export_type"] == "html":
    #             fig.write_html(f"{basename}.html")
    #         else:
    #             pio.write_image(
    #                 fig,
    #                 f"{basename}.{style['export_type']}",
    #                 width=plot_width,
    #                 height=plot_height,
    #             )
    #     return fig