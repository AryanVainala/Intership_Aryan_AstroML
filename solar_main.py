from solar_plotter import SolarPlotter

if __name__ == "__main__":
    plotter = SolarPlotter(sharp=True, aarp=True)
    
    plot_type = input("Would you like to plot an animation or a static plot? (animation/static): ").strip().lower()

    if plot_type == "animation":
        plotter.plot_animation()
    else:
        plotter.plot_data()