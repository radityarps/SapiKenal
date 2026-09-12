package id.sapikenal.app

import android.os.Bundle
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.appcompat.app.AppCompatActivity
import androidx.compose.runtime.getValue
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import dagger.hilt.android.AndroidEntryPoint
import id.sapikenal.app.data.local.SettingsDataStore
import id.sapikenal.app.data.local.dataStore
import id.sapikenal.app.ui.navigation.SapiKenalNavHost
import id.sapikenal.app.ui.theme.SapiKenalTheme
import kotlinx.coroutines.flow.map

@AndroidEntryPoint
class MainActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        enableEdgeToEdge()
        setContent {
            val textSizeMode by applicationContext.dataStore.data
                .map { prefs -> prefs[SettingsDataStore.KEY_TEXT_SIZE] ?: "system" }
                .collectAsStateWithLifecycle(initialValue = "system")

            SapiKenalTheme(textSizeMode = textSizeMode) {
                SapiKenalNavHost()
            }
        }
    }
}
