"""Union type of all plugin configuration models.

When adding a new plugin, import its Config here and extend the Union:
    PluginConfig = InspireConfig | SchemaOrgConfig | NewPluginConfig
"""

from middleware.inspire.config import Config as InspireConfig
from middleware.schema_org.config import Config as SchemaOrgConfig

# Union of all plugin config types. Used as the return type of
# RepositoryConfig.plugin_config and as the parameter type of all run_plugin functions.
PluginConfig = InspireConfig | SchemaOrgConfig
