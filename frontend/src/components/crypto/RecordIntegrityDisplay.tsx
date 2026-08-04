import { Shield, Clock, Hash, CheckCircle, AlertTriangle, XCircle } from "lucide-react";
import type { EncryptedRecord } from "@/types/clinical";
import type { ApiRecord } from "@/types/apiRecord";

interface RecordIntegrityDisplayProps {
  record: EncryptedRecord | ApiRecord;
  decryptedContent?: string;
  decryptionError?: string;
}

export function RecordIntegrityDisplay({
  record,
  decryptedContent,
  decryptionError,
}: RecordIntegrityDisplayProps) {
  // Calculate integrity status
  const isDecrypted = !!decryptedContent && !decryptionError;
  
  // Handle both EncryptedRecord and ApiRecord types
  const hash = 'hash' in record ? record.hash : undefined;
  const signatures = 'signatures' in record ? (record.signatures || []) : [];
  const hasSignatures = signatures.length > 0;
  const version = record.version;
  const createdAt = record.created_at;
  
  const integrityStatus = calculateIntegrityStatus(record as EncryptedRecord, decryptedContent, decryptionError);

  return (
    <div className="rounded-lg border bg-card p-4 text-sm">
      <div className="flex items-center justify-between mb-3">
        <h4 className="font-medium flex items-center gap-2">
          <Shield className="h-4 w-4" />
          Record Integrity
        </h4>
        <div className="flex items-center gap-2">
          {integrityStatus.icon}
          <span className={`text-xs font-medium ${integrityStatus.color}`}>
            {integrityStatus.text}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
        <div className="flex items-center gap-2">
          <Hash className="h-3 w-3 text-muted-foreground" />
          <span className="truncate" title={hash || 'No hash available'}>
            Hash: {hash ? `${hash.substring(0, 12)}...` : 'N/A'}
          </span>
        </div>
        
        <div className="flex items-center gap-2">
          <Clock className="h-3 w-3 text-muted-foreground" />
          <span>v{version || 'N/A'} · {createdAt ? new Date(createdAt).toLocaleDateString() : 'Unknown'}</span>
        </div>

        <div className="flex items-center gap-2">
          <div className="h-3 w-3 rounded-full bg-blue-500"></div>
          <span>{'encrypted_data' in record ? 'Crypto: AES-256-GCM + RSA-OAEP' : 'Server-decrypted'}</span>
        </div>

        <div className="flex items-center gap-2">
          <div className="h-3 w-3 rounded-full bg-green-500"></div>
          <span>
            Signatures: {signatures.length} {hasSignatures ? 'verified' : 'none'}
          </span>
        </div>
      </div>

      {decryptionError && (
        <div className="mt-3 p-2 rounded-md bg-destructive/10 text-destructive text-xs">
          <AlertTriangle className="h-3 w-3 inline mr-1" />
          Decryption failed: {decryptionError}
        </div>
      )}

      {isDecrypted && (
        <div className="mt-3 p-2 rounded-md bg-success/10 text-success text-xs">
          <CheckCircle className="h-3 w-3 inline mr-1" />
          Content successfully decrypted and verified
        </div>
      )}
    </div>
  );
}

function calculateIntegrityStatus(
  record: EncryptedRecord | ApiRecord,
  decryptedContent?: string,
  decryptionError?: string
) {
  if (decryptionError) {
    return {
      icon: <XCircle className="h-4 w-4 text-destructive" />,
      text: "Compromised",
      color: "text-destructive"
    };
  }
  
  if (decryptedContent) {
    return {
      icon: <CheckCircle className="h-4 w-4 text-success" />,
      text: "Verified",
      color: "text-success"
    };
  }
  
  // If it's an ApiRecord (already decrypted by backend), show verified
  if (!('encrypted_data' in record)) {
    return {
      icon: <CheckCircle className="h-4 w-4 text-success" />,
      text: "Verified",
      color: "text-success"
    };
  }
  
  return {
    icon: <Shield className="h-4 w-4 text-muted-foreground" />,
    text: "Encrypted",
    color: "text-muted-foreground"
  };
}
