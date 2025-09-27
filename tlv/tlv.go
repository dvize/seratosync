package tlv

import (
	"bytes"
	"encoding/binary"
	"fmt"
	"io"

	"golang.org/x/text/encoding/unicode"
	"golang.org/x/text/transform"
)

// Chunk represents a TLV chunk.
type Chunk struct {
	Tag   string
	Size  uint32
	Value []byte
}

// MakeChunk creates a TLV chunk as a byte slice.
func MakeChunk(tag string, payload []byte) []byte {
	tagBytes := []byte(tag)
	lengthBytes := make([]byte, 4)
	binary.BigEndian.PutUint32(lengthBytes, uint32(len(payload)))
	return append(append(tagBytes, lengthBytes...), payload...)
}

// WriteChunk writes a TLV chunk to an io.Writer.
func WriteChunk(writer io.Writer, tag string, payload []byte) error {
	chunk := MakeChunk(tag, payload)
	_, err := writer.Write(chunk)
	return err
}

// EncodeU16BE encodes a string to UTF-16BE.
func EncodeU16BE(s string) ([]byte, error) {
	encoder := unicode.UTF16(unicode.BigEndian, unicode.IgnoreBOM).NewEncoder()
	return encoder.Bytes([]byte(s))
}

// DecodeU16BE decodes a UTF-16BE byte slice to a string.
func DecodeU16BE(b []byte) (string, error) {
	reader := transform.NewReader(bytes.NewReader(b), unicode.UTF16(unicode.BigEndian, unicode.IgnoreBOM).NewDecoder())
	result, err := io.ReadAll(reader)
	if err != nil {
		return "", err
	}
	return string(result), nil
}

// IterTLV reads TLV chunks from an io.Reader.
func IterTLV(reader io.Reader) ([]*Chunk, error) {
	var chunks []*Chunk
	for {
		header := make([]byte, 8)
		_, err := io.ReadFull(reader, header)
		if err == io.EOF {
			break
		} else if err != nil {
			return nil, fmt.Errorf("failed to read chunk header: %w", err)
		}

		tag := string(header[0:4])
		size := binary.BigEndian.Uint32(header[4:8])

		value := make([]byte, size)
		_, err = io.ReadFull(reader, value)
		if err != nil {
			return nil, fmt.Errorf("failed to read chunk value for tag %s: %w", tag, err)
		}

		chunks = append(chunks, &Chunk{Tag: tag, Size: size, Value: value})
	}
	return chunks, nil
}

// IterNestedTLV iterates over nested TLV chunks in a byte slice.
func IterNestedTLV(buf []byte) ([]*Chunk, error) {
	var chunks []*Chunk
	pos := 0
	n := len(buf)
	for pos+8 <= n {
		tag := string(buf[pos : pos+4])
		size := binary.BigEndian.Uint32(buf[pos+4 : pos+8])
		start := pos + 8
		end := start + int(size)
		if end > n {
			break
		}
		chunks = append(chunks, &Chunk{Tag: tag, Size: uint32(size), Value: buf[start:end]})
		pos = end
	}
	return chunks, nil
}