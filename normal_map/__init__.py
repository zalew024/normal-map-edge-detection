from krita import DockWidgetFactory, DockWidgetFactoryBase
from .normal_map_docker import NormalMapDocker

DOCKER_ID = "Normal Map (Edge Detection)"
instance = Krita.instance()
dock_widget_factory = DockWidgetFactory(
    DOCKER_ID, DockWidgetFactoryBase.DockRight, NormalMapDocker
)

instance.addDockWidgetFactory(dock_widget_factory)
