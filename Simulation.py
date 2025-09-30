import customtkinter as ctk
from tkinter import ttk
import platform, os, numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from skyfield.api import load, wgs84
from tleFiles.makeTleFile import makeTle
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
from visibleSats import calcVisibleSats
import tkinter.messagebox as msgbox


class Simulator(ctk.CTk):
    def __init__(self):
        super().__init__()
        if platform.system() == "Windows":
            self.state("zoomed")
            self.update()
        else:
            self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}+0+0")
        ctk.set_appearance_mode("dark")

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2a2d2e", foreground="white", fieldbackground="#2a2d2e", rowheight=20)
        style.configure("Treeview.Heading", background="#565b5e", foreground="white", relief="flat")

        self.selectedPoint = None
        self.create_widgets()

    def create_widgets(self):
        mainFrame = ctk.CTkFrame(self)
        mainFrame.pack(fill="both", expand=True)
        mainFrame.grid_columnconfigure(0, weight=3)
        mainFrame.grid_columnconfigure(1, weight=1)

        mapFrame = ctk.CTkFrame(mainFrame)
        mapFrame.grid(row=0, column=0, sticky="nsew")

        self.fig = plt.Figure(figsize=(10, 5))
        self.ax = self.fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
        self.canvas = FigureCanvasTkAgg(self.fig, master=mapFrame)
        self.canvas.draw()
        toolbar = NavigationToolbar2Tk(self.canvas, mapFrame)
        toolbar.pack(side="top", fill="x")
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        self.canvas.mpl_connect("button_press_event", self.onRightClick)

        self.drawMap()

        self.latChoice = ctk.CTkEntry(mapFrame, placeholder_text="Lat", width=250)
        self.latChoice.pack(padx=2, pady=5, side="left")
        self.lonChoice = ctk.CTkEntry(mapFrame, placeholder_text="Lon", width=250)
        self.lonChoice.pack(padx=2, pady=5, side="left")

        self.setPositionBtn = ctk.CTkButton(
            mapFrame,
            text="Set Position",
            command=lambda: self.updatePosition(float(self.latChoice.get()), float(self.lonChoice.get())),
        )
        self.setPositionBtn.pack(side="left", pady=5, padx=5)

        self.minAngle = ctk.CTkEntry(mapFrame, placeholder_text="Min elevation angle", width=200)
        self.minAngle.pack(padx=5, pady=5)
        self.maxAngle = ctk.CTkEntry(mapFrame, placeholder_text="Max elevation angle", width=200)
        self.maxAngle.pack(padx=5, pady=5)

        self.calcVisibleBtn = ctk.CTkButton(mapFrame, text="export visible sats excel", command=self.calcVisibleSatsChoice)
        self.calcVisibleBtn.pack(pady=5, padx=5)

        rightFrame = ctk.CTkFrame(mainFrame)
        rightFrame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        self.searchSat = ctk.CTkEntry(rightFrame, placeholder_text="Search satellite:")
        self.searchSat.pack(fill="x", pady=(0, 5))
        self.searchSat.bind("<KeyRelease>", self.onSearch)

        tablesValues = ["Gnss", "Gps", "Beidou", "Cosmos", "Constellation"]
        self.tableChoice = ctk.StringVar(value="Gnss")
        self.tableOptions = ctk.CTkOptionMenu(rightFrame, variable=self.tableChoice, values=tablesValues, command=self.onChoice)
        self.tableOptions.pack(fill="x", pady=(0, 5))
        self.table = self.createTable(rightFrame, self.tableChoice, ("satNumber", "satName"), self.onSelectAll)

        self.resetButton = ctk.CTkButton(rightFrame, text="Reset", command=self.onReset)
        self.resetButton.pack(fill="x", pady=(5, 0))

        self.label = ctk.CTkLabel(rightFrame, text="Update every (2 sec is defult):").pack(pady=5, padx=5, side="left")
        self.updateTime = ctk.CTkEntry(rightFrame, width=200)
        self.updateTime.pack(pady=(5, 0))

        self.selectedNames = set()
        self.satellites = self.downloadTleData(self.tableChoice.get())
        self.filteredSatellites = self.satellites
        self.updateTable(self.table, self.satellites)
        self.startAutoUpdate()

    def createTable(self, parent, title, columns, command):
        label = ctk.CTkLabel(parent, textvariable=title)
        label.pack(fill="x")

        table = ttk.Treeview(parent, columns=columns, show="headings")
        for col in columns:
            table.heading(col, text=col)
        table.pack(fill="both", expand=True)
        table.bind("<Double-1>", lambda event: self.onSatClick(event, table))

        button = ctk.CTkButton(parent, text="Select All", command=lambda: command(table))
        button.pack(fill="x", pady=(5, 0))
        return table

    def onChoice(self, choice):
        self.satellites = self.downloadTleData(choice)
        self.filteredSatellites = self.satellites
        self.updateTable(self.table, self.filteredSatellites)

    def downloadTleData(self, choice):
        urls = {"Gnss": "gnss", "Gps": "gps-ops", "Beidou": "beidou", "Cosmos": "musson"}
        if choice == "Constellation":
            makeTle()
            satellites = load.tle_file("tleFiles/constellation.txt")
        else:
            os.makedirs("tleFiles", exist_ok=True)
            tleUrl = f"http://www.celestrak.org/NORAD/elements/gp.php?GROUP={urls[choice]}&FORMAT=tle"
            satellites = load.tle_file(tleUrl, filename=f"tleFiles/{choice}.txt")
        return satellites

    def updateTable(self, table, satellites):
        table.delete(*table.get_children())

        for i, sat in enumerate(satellites):
            item_id = table.insert("", "end", values=(i + 1, sat.name))
            if sat.name in self.selectedNames:
                table.item(item_id, tags=("selected",))

        table.tag_configure("selected", background="#22559b")
        self.plotSats()

    def onSearch(self, event):
        query = self.searchSat.get().lower()
        if query == "":
            self.filteredSatellites = self.satellites
        else:
            self.filteredSatellites = [sat for sat in self.satellites if query in sat.name.lower()]
        self.updateTable(self.table, self.filteredSatellites)

    def onSatClick(self, event, table):
        item = table.identify_row(event.y)
        satName = table.item(item, "values")[1]

        if satName in self.selectedNames:
            self.selectedNames.remove(satName)
            table.item(item, tags=())

            self.clearSelection()
        else:
            self.selectedNames.add(satName)
            table.item(item, tags=("selected",))
        self.plotSats()

    def plotSats(self):
        if hasattr(self, "satArtists") or hasattr(self, "satLabels"):
            for artist in list(self.satArtists.keys()):
                try:
                    artist.remove()
                except Exception:
                    pass
            for label in self.satLabels:
                try:
                    label.remove()
                except Exception:
                    pass

        ts = load.timescale()
        t = ts.now()

        self.satArtists = {}
        self.satLabels = []

        for sat in self.satellites:
            if sat.name in self.selectedNames:
                geo = sat.at(t)
                subpoint = wgs84.subpoint(geo)
                lon, lat = subpoint.longitude.degrees, subpoint.latitude.degrees

                artist = self.ax.plot(lon, lat, "bo", markersize=5, picker=5)[0]
                self.satArtists[artist] = sat
                label = self.ax.text(lon + 0.5, lat + 0.5, sat.name, fontsize=8, color="black")
                self.satLabels.append(label)

        self.canvas.draw()
        self.canvas.mpl_connect("pick_event", self.onPick)

    def onPick(self, event):
        artist = event.artist
        if artist in self.satArtists:
            sat = self.satArtists[artist]

            self.clearSelection()

            x, y = artist.get_data()
            self.highlight = self.ax.plot(x, y, "o", markersize=18, markeredgecolor="black", markerfacecolor="none")[0]

            # חישוב מסלול עתידי
            ts = load.timescale()
            now = ts.now()
            start = now.utc_datetime()
            minutes = range(start.minute, start.minute + 12 * 60)
            times = ts.utc(start.year, start.month, start.day, start.hour, minutes)

            lons, lats = [], []
            for t in times:
                geo = sat.at(t)
                subpoint = wgs84.subpoint(geo)
                lons.append(subpoint.longitude.degrees)
                lats.append(subpoint.latitude.degrees)

            lons = np.array(lons)
            for i in range(1, len(lons)):
                if lons[i] - lons[i - 1] > 180:
                    lons[i:] -= 360
                elif lons[i] - lons[i - 1] < -180:
                    lons[i:] += 360

            self.trajectory = self.ax.plot(lons, lats, "b-", linewidth=3)[0]
            self.canvas.draw()

    def onReset(self):
        self.selectedNames.clear()
        self.table.selection_remove(*self.table.selection())

        for rowId in self.table.get_children():
            self.table.item(rowId, tags=())

        self.clearSelection()
        self.selectedPoint = None
        self.latChoice.delete(0, "end"), self.latChoice.configure(placeholder_text="Lat")
        self.lonChoice.delete(0, "end"), self.lonChoice.configure(placeholder_text="Lon")
        self.searchSat.delete(0, "end"), self.searchSat.configure(placeholder_text="Search satellite:")
        self.drawMap(preserve_view=False)

    def drawMap(self, preserve_view=True):
        if preserve_view:
            xlim = self.ax.get_xlim()
            ylim = self.ax.get_ylim()

        self.ax.clear()
        self.ax.stock_img()
        self.ax.coastlines()
        self.ax.add_feature(cfeature.BORDERS)

        if preserve_view:
            self.ax.set_xlim(xlim)
            self.ax.set_ylim(ylim)
        self.canvas.draw()

    def startAutoUpdate(self):
        try:
            interval = int(float(self.updateTime.get()) * 1000)
        except ValueError:
            interval = 2000

        self.updateTable(self.table, self.filteredSatellites)
        self.after(interval, self.startAutoUpdate)

    def onSelectAll(self, table):
        for rowId in table.get_children():
            satName = table.item(rowId, "values")[1]
            self.selectedNames.add(satName)
            table.item(rowId, tags=("selected",))

        self.clearSelection()
        self.plotSats()

    def onRightClick(self, event):
        if platform.system() == "Darwin" and event.button == 2 or platform.system() == "Windows" and event.button == 3:
            if event.xdata is not None and event.ydata is not None:
                self.updatePosition(event.ydata, event.xdata)

    def updatePosition(self, lat, lon):
        self.latChoice.delete(0, "end"), self.latChoice.insert(0, f"{lat:.2f}")
        self.lonChoice.delete(0, "end"), self.lonChoice.insert(0, f"{lon:.2f}")

        if getattr(self, "selectedPointArtist", None) is not None:
            self.selectedPointArtist.remove()

        self.selectedPointArtist = self.ax.plot(lon, lat, "rx", markersize=10)[0]
        self.selectedPoint = (lon, lat)
        self.canvas.draw()

    def calcVisibleSatsChoice(self):
        try:
            lat = float(self.latChoice.get())
            lon = float(self.lonChoice.get())
            minAngle = float(self.minAngle.get())
            maxAngle = float(self.maxAngle.get())
        except ValueError:
            msgbox.showerror("Error", "Please enter valid data")
            return

        if not (0 <= minAngle <= 90) or not (0 <= maxAngle <= 90):
            msgbox.showerror("Error", "Angles must be between 0 and 90 degrees.")
            return

        if minAngle > maxAngle:
            msgbox.showerror("Error", "Minimum angle cannot be greater than maximum angle.")
            return

        if self.selectedPoint is None:
            msgbox.showerror("Error", "Please set a position first.")
            return

        calcVisibleSats(lat, lon, minAngle, maxAngle)
        msgbox.showinfo("Success", "Visible satellites exported to 'visibleSats.csv'")

    def clearSelection(self):
        if getattr(self, "trajectory", None) is not None:
            self.trajectory.remove()
            self.trajectory = None
        if getattr(self, "highlight", None) is not None:
            self.highlight.remove()
            self.highlight = None
        if getattr(self, "selectedPointArtist", None) is not None:
            self.selectedPointArtist.remove()
            self.selectedPointArtist = None


if __name__ == "__main__":
    app = Simulator()
    app.bind("<Control-w>", lambda event: app.destroy())
    app.mainloop()
