package id.sapikenal.app.ui.camera

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.NotInterested
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.rememberModalBottomSheetState
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import id.sapikenal.app.R
import id.sapikenal.app.domain.model.DetectionResult
import id.sapikenal.app.ui.theme.SapiKenalColors

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun NonCattleRejectionSheet(
    rejection: DetectionResult,
    onRetake: () -> Unit,
    onChooseAnother: () -> Unit,
    onDismiss: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val sheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true)

    ModalBottomSheet(
        onDismissRequest = onDismiss,
        sheetState = sheetState,
        containerColor = SapiKenalColors.Surface,
        shape = RoundedCornerShape(topStart = 24.dp, topEnd = 24.dp),
        modifier = modifier,
    ) {
        Column(
            modifier =
                Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 24.dp)
                    .padding(bottom = 32.dp, top = 8.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            // Rejection Icon
            Box(
                modifier =
                    Modifier
                        .size(64.dp)
                        .clip(CircleShape)
                        .background(SapiKenalColors.SurfaceVariant),
                contentAlignment = Alignment.Center,
            ) {
                Icon(
                    imageVector = Icons.Outlined.NotInterested,
                    contentDescription = null,
                    modifier = Modifier.size(32.dp),
                    tint = SapiKenalColors.TextSecondary,
                )
            }

            Spacer(modifier = Modifier.height(16.dp))

            // Rejection status badge
            Surface(
                shape = RoundedCornerShape(8.dp),
                color = SapiKenalColors.SurfaceVariant,
            ) {
                Text(
                    text = stringResource(R.string.rejection_status_badge),
                    style = MaterialTheme.typography.labelMedium,
                    fontWeight = FontWeight.SemiBold,
                    color = SapiKenalColors.TextSecondary,
                    modifier = Modifier.padding(horizontal = 10.dp, vertical = 4.dp),
                )
            }

            Spacer(modifier = Modifier.height(12.dp))

            // Title
            Text(
                text = stringResource(R.string.rejection_non_cattle_title),
                style = MaterialTheme.typography.headlineSmall,
                fontWeight = FontWeight.Bold,
                textAlign = TextAlign.Center,
                color = SapiKenalColors.TextPrimary,
                modifier = Modifier.semantics { heading() },
            )

            Spacer(modifier = Modifier.height(8.dp))

            // Description
            Text(
                text = stringResource(R.string.rejection_non_cattle_desc),
                style = MaterialTheme.typography.bodyMedium,
                textAlign = TextAlign.Center,
                color = SapiKenalColors.TextSecondary,
                modifier = Modifier.fillMaxWidth(),
            )

            if (rejection.confidence > 0f) {
                Spacer(modifier = Modifier.height(8.dp))
                val confidencePct = (rejection.confidence * 100).toInt()
                Text(
                    text = stringResource(R.string.rejection_confidence_label, confidencePct),
                    style = MaterialTheme.typography.bodySmall,
                    color = SapiKenalColors.TextSecondary,
                    fontSize = 12.sp,
                )
            }

            Spacer(modifier = Modifier.height(24.dp))

            // Primary Action: Retake Photo
            Button(
                onClick = {
                    onDismiss()
                    onRetake()
                },
                modifier =
                    Modifier
                        .fillMaxWidth()
                        .height(50.dp),
                shape = RoundedCornerShape(12.dp),
                colors =
                    ButtonDefaults.buttonColors(
                        containerColor = SapiKenalColors.Primary,
                        contentColor = SapiKenalColors.OnPrimary,
                    ),
            ) {
                Text(
                    text = stringResource(R.string.rejection_btn_retake),
                    style = MaterialTheme.typography.labelLarge,
                    fontWeight = FontWeight.SemiBold,
                )
            }

            Spacer(modifier = Modifier.height(10.dp))

            // Secondary Action: Choose from Gallery
            OutlinedButton(
                onClick = {
                    onDismiss()
                    onChooseAnother()
                },
                modifier =
                    Modifier
                        .fillMaxWidth()
                        .height(50.dp),
                shape = RoundedCornerShape(12.dp),
            ) {
                Text(
                    text = stringResource(R.string.rejection_btn_gallery),
                    style = MaterialTheme.typography.labelLarge,
                    fontWeight = FontWeight.SemiBold,
                    color = SapiKenalColors.Primary,
                )
            }

            Spacer(modifier = Modifier.height(6.dp))

            // Tertiary Action: Dismiss
            TextButton(
                onClick = onDismiss,
                modifier = Modifier.fillMaxWidth(),
            ) {
                Text(
                    text = stringResource(R.string.rejection_btn_back),
                    style = MaterialTheme.typography.labelLarge,
                    color = SapiKenalColors.TextSecondary,
                )
            }
        }
    }
}
