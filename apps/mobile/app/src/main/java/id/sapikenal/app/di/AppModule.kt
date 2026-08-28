package id.sapikenal.app.di

import android.content.Context
import android.net.ConnectivityManager
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import id.sapikenal.app.data.local.SettingsDataStore
import id.sapikenal.app.location.DefaultLocationProvider
import id.sapikenal.app.location.LocationProvider
import id.sapikenal.app.ml.DefaultNetworkChecker
import id.sapikenal.app.ml.ImageClassifier
import id.sapikenal.app.ml.ImagePreprocessor
import id.sapikenal.app.ml.NetworkChecker
import id.sapikenal.app.ml.OfflineInferenceEngine
import id.sapikenal.app.ml.OnlineInferenceClient
import id.sapikenal.app.ml.preprocessing.ClientPreprocessor
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object AppModule {
    @Provides
    fun provideConnectivityManager(
        @ApplicationContext context: Context,
    ): ConnectivityManager = context.getSystemService(ConnectivityManager::class.java)

    @Provides
    @Singleton
    fun provideNetworkChecker(connectivityManager: ConnectivityManager): NetworkChecker = DefaultNetworkChecker(connectivityManager)

    @Provides
    @Singleton
    fun provideImagePreprocessor(clientPreprocessor: ClientPreprocessor): ImagePreprocessor = clientPreprocessor

    @Provides
    @Singleton
    @OnlineClassifier
    fun provideOnlineClassifier(onlineClient: OnlineInferenceClient): ImageClassifier = onlineClient

    @Provides
    @Singleton
    @OfflineClassifier
    fun provideOfflineClassifier(offlineEngine: OfflineInferenceEngine): ImageClassifier = offlineEngine

    @Provides
    @Singleton
    fun provideSettingsDataStore(
        @ApplicationContext context: Context,
    ): SettingsDataStore = SettingsDataStore(context)

    @Provides
    @Singleton
    fun provideLocationProvider(defaultLocationProvider: DefaultLocationProvider): LocationProvider = defaultLocationProvider
}
