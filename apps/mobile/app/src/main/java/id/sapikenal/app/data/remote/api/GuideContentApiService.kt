package id.sapikenal.app.data.remote.api

import id.sapikenal.app.data.remote.dto.GuideSnapshotDto
import retrofit2.http.GET
import retrofit2.http.Query

interface GuideContentApiService {
    @GET("api/content/articles")
    suspend fun articles(
        @Query("locale") locale: String? = null,
    ): GuideSnapshotDto
}
