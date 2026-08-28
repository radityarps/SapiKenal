package id.sapikenal.app.data.remote.api

import id.sapikenal.app.data.remote.dto.HealthResponseDto
import id.sapikenal.app.data.remote.dto.HistorySyncRequestDto
import id.sapikenal.app.data.remote.dto.PredictResponseDto
import okhttp3.MultipartBody
import okhttp3.ResponseBody
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.Multipart
import retrofit2.http.POST
import retrofit2.http.Part

interface InferenceApiService {
    @Multipart
    @POST("api/predict")
    suspend fun predict(
        @Part image: MultipartBody.Part,
    ): PredictResponseDto

    @GET("api/health")
    suspend fun health(): HealthResponseDto

    @POST("api/history")
    suspend fun upsertHistory(
        @Body payload: HistorySyncRequestDto,
    ): Response<ResponseBody>
}
